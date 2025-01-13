package temptoken

import (
	"errors"
	"fmt"

	red "github.com/redis/go-redis/v9"

	"context"
)

type Repository interface {
	GetToken(ctx context.Context, user string) (token string, err error)
	SetToken(ctx context.Context, user, token string) (err error)
	ResetToken(ctx context.Context, user string) (err error)
}

type repo struct {
	r *red.Client
}

func NewRepo(r *red.Client) Repository {
	return &repo{r}
}

var _ Repository = &repo{}

const unameFmt = "temp_token/%s"

// GetToken implements Repository.
func (r *repo) GetToken(ctx context.Context, user string) (token string, err error) {
	res, err := r.r.Get(ctx, fmt.Sprintf(unameFmt, user)).Result()
	if err != nil && err != red.Nil {
		return "", errors.New("sorry get failed idk why")
	}

	return res, nil
}

// ResetToken implements Repository.
func (r *repo) ResetToken(ctx context.Context, user string) (err error) {
	err = r.r.Del(ctx, fmt.Sprintf(unameFmt, user)).Err()
	if err != nil && err != red.Nil {
		return err
	}

	return nil

}

// SetToken implements Repository.
func (r *repo) SetToken(ctx context.Context, user string, token string) (err error) {
	err = r.r.Set(ctx, fmt.Sprintf(unameFmt, user), token, red.KeepTTL).Err()
	if err != nil && err != red.Nil {
		return err
	}

	return nil
}
