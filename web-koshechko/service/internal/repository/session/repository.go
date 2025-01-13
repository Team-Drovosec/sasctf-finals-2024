package session

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"time"

	red "github.com/redis/go-redis/v9"
)

type Repository interface {
	GetUsername(ctx context.Context, token string) (username string, err error)
	IsValid(ctx context.Context, token string) bool
	DeleteSession(ctx context.Context, token string) error

	Identify(ctx context.Context, user string) (token string, err error)
	Auth(ctx context.Context, token string) (err error)
}

type repo struct {
	r *red.Client
}

func NewRepo(r *red.Client) Repository {
	return repo{r}
}

const unameFmt = "token/%s/username"
const authenticatedFmt = "authenticated/%s/username"

// DeleteSession implements Repository.
func (s repo) DeleteSession(ctx context.Context, token string) error {
	_, err := s.r.Del(ctx, fmt.Sprintf(authenticatedFmt, token)).Result()
	if err != nil && err != red.Nil {
		return err
	}

	_, err = s.r.Del(ctx, fmt.Sprintf(unameFmt, token)).Result()
	if err != nil && err != red.Nil {
		return err
	}

	return nil

}

func (s repo) GetUsername(ctx context.Context, token string) (username string, err error) {
	res, err := s.r.Get(ctx, fmt.Sprintf(unameFmt, token)).Result()
	if err != nil && err != red.Nil {
		return "", errors.New("sorry session check failed idk why")
	}

	return res, nil
}

func (s repo) IsValid(ctx context.Context, token string) bool {
	_, err := s.r.Get(ctx, fmt.Sprintf(authenticatedFmt, token)).Result()
	if err != nil && err != red.Nil {
		return false
	}

	return true
}

func generateToken() (string, error) {
	bytes := make([]byte, 16)
	if _, err := rand.Read(bytes); err != nil {
		return "", err
	}
	return hex.EncodeToString(bytes), nil

}

func (s repo) Identify(ctx context.Context, user string) (token string, err error) {
	token, err = generateToken()
	if err != nil && err != red.Nil {
		return "", err
	}

	err = s.r.Set(ctx, fmt.Sprintf(unameFmt, token), user, time.Minute*15).Err()
	if err != nil && err != red.Nil {
		return "", err
	}

	return token, nil
}

func (s repo) Auth(ctx context.Context, token string) (err error) {
	err = s.r.Set(ctx, fmt.Sprintf(authenticatedFmt, token), "true", time.Minute*15).Err()
	if err != nil && err != red.Nil {
		return err
	}

	return nil
}
