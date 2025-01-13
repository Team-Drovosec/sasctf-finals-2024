package koshechko

import (
	"context"
	"errors"
	"koshechko/internal/database"
	"koshechko/internal/service/model"
)

type Repository interface {
	Create(ctx context.Context,
		Name string,
		owner string,
		text string,
		sharedWith []string,
	) (id int64, err error)
	Delete(ctx context.Context, name string) error
	Get(ctx context.Context, name string) (model.Koshechko, error)
	Update(ctx context.Context, oldName, name, text string, sharedWith []string) error
}

type koshechko struct {
	qe database.QueryExecutor
}

func New(executor database.QueryExecutor) Repository {
	return koshechko{qe: executor}
}

func (k koshechko) Create(ctx context.Context, name, owner string, text string, sharedWith []string) (int64, error) {
	if len(sharedWith) > 40 {
		return 0, errors.New("too much publicity")
	}
	var id int64
	err := k.qe.QueryRow(ctx, "insert into koshechko (name, owner, text, shared_with) values ($1, $2, $3, $4) returning id", name, owner, text, sharedWith).Scan(&id)
	if err != nil {
		return 0, errors.New("failed to create koshechko idk why")
	}

	return id, nil
}

func (k koshechko) Delete(ctx context.Context, name string) error {
	_, err := k.qe.Exec(ctx, "delete from koshechko where name = $1", name)
	if err != nil {
		return errors.New("failed to delete koshechko idk why")
	}

	return nil
}

func (k koshechko) Update(ctx context.Context, oldName, name, text string, sharedWith []string) error {
	if len(sharedWith) > 40 {
		return errors.New("too much publicity")
	}
	_, err := k.qe.Exec(ctx, "update koshechko set name= $2, text = $3, shared_with = $4 where name = $1", oldName, name, text, sharedWith)
	if err != nil {
		return errors.New("failed to udpate koshechko idk why")
	}

	return nil
}

func (k koshechko) Get(ctx context.Context, name string) (model.Koshechko, error) {
	res := model.Koshechko{}
	err := k.qe.QueryRow(ctx, "select id, name, owner, text, shared_with from koshechko where name = $1", name).
		Scan(&res.ID, &res.Name, &res.Owner, &res.Text, &res.SharedWith)
	if err != nil {
		return model.Koshechko{}, err
	}
	return res, nil
}
