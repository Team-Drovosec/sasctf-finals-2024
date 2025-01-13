package lb

import (
	"context"
	"fmt"
	"koshechko/internal/service/model"
	"time"

	red "github.com/redis/go-redis/v9"
	"golang.org/x/sync/errgroup"
)

type (
	Repository interface {
		TopKoshechko(ctx context.Context) ([]model.LBKoshechko, error)
		KoshechkoRank(ctx context.Context, koshechkoName string) (int64, error)
		UserRank(ctx context.Context, username string) (int64, error)
		KoshechkoScore(ctx context.Context, koshechkoName string) (int64, error)
		UserScore(ctx context.Context, username string) (int64, error)
		TopUsers(ctx context.Context) ([]model.LBUser, error)
		IncKoshechko(ctx context.Context, koshechkoName string) error
		IncUser(ctx context.Context, username string) error
		DelKoshechko(ctx context.Context, kosheckoName string) error
		DelUser(ctx context.Context, username string) error
	}

	lb struct {
		r *red.Client
	}
)

func NewLB(r *red.Client) lb {
	return lb{
		r: r,
	}
}

func (l lb) TopUsers(ctx context.Context) ([]model.LBUser, error) {
	return top[model.LBUser](
		ctx,
		l.r,
		usersLB,
		l.rank,
		func(val string, score, rank int64) model.LBUser {
			return model.LBUser{
				Username: val,
				Score:    score,
				Rank:     rank,
			}
		},
	)
}

func (l lb) TopKoshechko(ctx context.Context) ([]model.LBKoshechko, error) {
	return top[model.LBKoshechko](
		ctx,
		l.r,
		koshechkoLB,
		l.rank,
		func(val string, score, rank int64) model.LBKoshechko {
			return model.LBKoshechko{
				Name:  val,
				Score: score,
				Rank:  rank,
			}
		},
	)
}

func (l lb) KoshechkoRank(ctx context.Context, koshechkoName string) (int64, error) {
	return l.rank(ctx, koshechkoLB, koshechkoName)
}

func (l lb) UserRank(ctx context.Context, username string) (int64, error) {
	return l.rank(ctx, usersLB, username)
}

func (l lb) KoshechkoScore(ctx context.Context, koshechkoName string) (int64, error) {
	return l.score(ctx, koshechkoLB, koshechkoName)
}

func (l lb) UserScore(ctx context.Context, username string) (int64, error) {
	return l.score(ctx, usersLB, username)
}

func (l lb) IncKoshechko(ctx context.Context, koshechkoName string) error {
	return l.inc(ctx, koshechkoLB, koshechkoName, 1)
}

func (l lb) IncUser(ctx context.Context, username string) error {
	return l.inc(ctx, usersLB, username, 1)
}

func (l lb) DelKoshechko(ctx context.Context, kosheckoName string) error {
	return l.del(ctx, koshechkoLB, kosheckoName)
}

func (l lb) DelUser(ctx context.Context, username string) error {
	return l.del(ctx, usersLB, username)
}

const (
	koshechkoLB = "koshechko"
	usersLB     = "users"
)

func (l lb) inc(ctx context.Context, schema, key string, value int64) error {
	err := l.r.ZIncrBy(ctx, schema, float64(value), key).Err()
	if err != nil {
		return err
	}

	return nil
}

func (l lb) rank(ctx context.Context, schema, key string) (int64, error) {
	uRank, err := l.r.ZRevRank(ctx, schema, key).Result()
	if err != nil && err != red.Nil {
		return 0, err
	}

	return uRank + 1, nil
}

func (l lb) score(ctx context.Context, schema, key string) (int64, error) {
	uRank, err := l.r.ZScore(ctx, schema, key).Result()
	if err != nil && err != red.Nil {
		return 0, err
	}

	return int64(uRank), nil
}

func (l lb) del(ctx context.Context, schema, key string) error {
	_, err := l.r.ZRem(ctx, schema, key).Result()
	if err != nil && err != red.Nil {
		return err
	}

	return nil
}

// i rly need generic methods
func top[T any](
	ctx context.Context,
	redis *red.Client,
	schema string,
	rankFn func(ctx context.Context, schema, key string) (int64, error),
	mapFn func(val string, score, rank int64) T,
) ([]T, error) {
	ctx, cancel := context.WithTimeout(ctx, time.Minute)
	defer cancel()

	vals, err := redis.ZRevRangeWithScores(ctx, schema, 0, 100000000000000).Result()
	if err != nil {
		return nil, err
	}

	us := make([]T, 0, 100)
	g, ctx := errgroup.WithContext(ctx)

	for _, v := range vals {
		v := v
		g.Go(func() error {
			val, ok := v.Member.(string)
			if !ok {
				return fmt.Errorf("failed to cast uid from redis")
			}

			rank, err := rankFn(ctx, schema, val)
			if err != nil {
				return err
			}

			us = append(us, mapFn(val, int64(v.Score), rank))

			return nil
		})

	}

	err = g.Wait()
	if err != nil {
		return nil, fmt.Errorf("failed to get topN: %w", err)
	}

	return us, nil

}
