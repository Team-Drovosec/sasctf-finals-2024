# Koshechko

![](../images/koshechko.webp)

## Description

Koshechko is a service about sharing Koshechko. You can create your private or public Koshechko and optionally share it with other users. Also, this service keeps track of how much Koshechko is shared to you, so everyone can know who has the most Koshechko. It uses a Postgres-based queue to update the scoreboard of users in Redis for optimal GET performance.

## Vulnerabilities

### 1. Insecure authentication checks

The login process consists of two steps (2FA): identification and authentication. Only by passing both checks users can access their Koshechko.

```go
// service.go
func (s *Service) CheckSession() gin.HandlerFunc {
	return func(c *gin.Context) {
		token := c.Request.Header.Get("token")
		username, err := s.session.GetUsername(c.Request.Context(), token)
		if err != nil || username == "" {
			c.AbortWithError(300, errors.New("username bad"))
		}
		c.Set(UsernameKey, username)

		isValid := s.session.IsValid(c.Request.Context(), token)
		c.Set(IsValidKey, isValid)
		c.Next()
	}
}
```

Koshechko view function also checks for authentication:
```go
// view.go
isValid := c.GetBool(IsValidKey)
if !isValid {
	c.AbortWithStatus(403)
	return
}
```

This is the code that checks if you are authenticated:
```go
// repository/session/repository.go
func (s repo) IsValid(ctx context.Context, token string) bool {
	_, err := s.r.Get(ctx, fmt.Sprintf(authenticatedFmt, token)).Result()
	if err != nil && err != red.Nil {
		return false
	}

	return true
}
```

If `err == red.nil` function returns `true`, so when no value (meaning `red.Nil` error) for a token is stored, the session authentication passes.

Exploiting this allows you to automatically pass authentication stage upon passing identification stage, allowing you to view any Koshechko.


### 2. Bypassing 2FA due to insecure hashing system

If user fails on authentication stage, it's session and the hash salt (token) is deleted:

```go
// login.go
if needHash != req.PasswordHash {
	slog.Error("wrong", "need", needHash, "req", req.PasswordHash)
	_ = s.session.DeleteSession(ctx, token)
	_ = s.tok.ResetToken(ctx, username)
	c.AbortWithStatus(333)

	return
}
```

Key for storing the token, as appears, is an username.

Then, if we look at the hashing code in `hash/hash.go` we can see that an empty string produces a hash that equals zero:

```go
// returns 0 for ""
func stringToBigInt(s string) (*big.Int, error) {
	if len(s) == 0 {
		return nil, nil
	}

	b := big.NewInt(int64(s[0]))
	for _, c := range s[1:] {
		b = b.Mul(b, big.NewInt(int64(c)))
	}
	return b, nil
}

func Hash(x string) (string, error) {
	inp, err := stringToBigInt(x)
	if err != nil {
		return "", err
	}

	c := big.NewInt(0)
	c = c.Exp(inp, e, n)
	// exp(0, e, n) = 0

	return c.String(), nil // "0"
}
```

These two factors allows us to play the following scenario:

1. Create two sessions (unfinished attempts to login) as user X
2. In one session send the wrong password to the `login` handler
3. Now, the temporary hash token is an empty string, as `temp_token/repository.go/GetToken()` ignores `red.Nil`
4. On the second session, try to login with password hash that equals zero
5. Authentication stage for the second session will pass due to the `hash.AddHash(string(u.PasswordHash), tok) == 0` as `tok == 0`


### 3. Race condition / Two-phase commit issue

Several operations in the service are handled in a separate work queue, handled in `process_lb.go`:
1. ETIncUser — increment user score
2. ETIncKoshechko — increment Koshechko score
3. ETDelKoshechko — deletion of Koshechko and it's score
4. ETDelUser — deletion of user and it's score
5. ETUpdateKoshechko — updating Koshechko, incrementing score of all users, for which this Koshechko is shared with

Score of a user equals the amount of Koshechko shared with them. Score of a Koshechko is the amount of users it is shared with. Public Koshechko have 0 points.

```go
// view.go
score, err := s.lb.KoshechkoScore(ctx, req.Name)
if err != nil {
	slog.Error("rank", err)
	c.AbortWithStatus(228)
	return
}
if score == model.PublicKoshechko {
	c.JSON(200, viewKoshechkoResp{
		...
	})
	return
}
```

The `Process` function uses `s.reg.InTx` to handle it's postgres operations in a single transaction. It means that if the transaction fails, all changes will be rolled back to their original state. ETDelKoshechko also uses redis to delete Koshechko score. Redis connection cannot use the postgresql transaction, so even if transaction is rolled back, changes in redis are preserved.

If you would fail the transaction when checker attempts to delete the Koshechko that contains a flag (which it intentionally does to check the delete functionality), Koshechko will become public (score == 0) until the `process_lb.go` worker will retry the deletion. 

To trigger the transaction failure we can rename Koshechko with a name that is already in use. 

The exploit is provided in `exploit/exploit.py`
