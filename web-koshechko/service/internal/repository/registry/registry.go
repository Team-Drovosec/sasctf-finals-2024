package registry

import (
	"context"
	"errors"
	"fmt"
	"koshechko/internal/database"
	"koshechko/internal/repository/koshechko"
	"koshechko/internal/repository/lb_queue"
	"koshechko/internal/repository/user"

	"github.com/jackc/pgx/v5"
	"go.uber.org/multierr"
)

// Ошибки выполнения транзакции
var (
	ErrBegin  = errors.New("begin tx")
	ErrExec   = errors.New("exec in tx")
	ErrCommit = errors.New("commit tx")
)

type (
	// InTransaction ...
	InTransaction func(repoRegistry RepoRegistry) error

	// RepoRegistry ...
	RepoRegistry interface {
		User() user.Repository
		Koshechko() koshechko.Repository
		LBQueue() lb_queue.Repository

		InTx(ctx context.Context, txFunc InTransaction) error
	}

	registry struct {
		db       database.QueryExecutor
		txHolder database.QueryExecutor
	}
)

// NewRepoRegistry ...
func NewRepoRegistry(qe database.QueryExecutor) RepoRegistry {
	return newRegistry(qe)
}

func newRegistry(db database.QueryExecutor) *registry {
	return &registry{
		db: db,
	}
}

// InTx ...
func (r registry) InTx(ctx context.Context, txFunc InTransaction) (err error) {
	var (
		tx  pgx.Tx
		reg registry
	)

	if r.txHolder == nil {
		tx, err = r.db.Begin(ctx)
		if err != nil {
			return fmt.Errorf("%v: %w", err, ErrBegin)
		}

		defer func() {
			if p := recover(); p != nil {
				_ = tx.Rollback(ctx)
				panic(p)
			} else if err != nil {
				err = multierr.Append(err, tx.Rollback(ctx))
			}
		}()

		reg = registry{
			db:       r.db,
			txHolder: tx,
		}
	}

	err = txFunc(reg)
	if err != nil {
		return fmt.Errorf("%v: %w", err, ErrExec)
	}

	if err = tx.Commit(ctx); err != nil {
		return fmt.Errorf("%v: %w", err, ErrCommit)
	}

	return nil
}
