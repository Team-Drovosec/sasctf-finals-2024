package user

import (
	"context"
	"errors"
	"koshechko/internal/database"
	"koshechko/internal/service/model"
)

type Repository interface {
	Save(ctx context.Context, user, password, description string) error
	Get(ctx context.Context, user string) (model.User, error)
	Update(ctx context.Context, user, description string) error
	Delete(ctx context.Context, user string) error
}

type user struct {
	qe database.QueryExecutor
}

func New(qe database.QueryExecutor) Repository {
	return user{qe: qe}
}

func (u user) Save(ctx context.Context, user, passwordHash, description string) error {
	_, err := u.qe.Exec(ctx, "insert into users (username, password, description) values ($1, $2, $3)", user, passwordHash, description)
	if err != nil {
		return errors.New("sorry user not created idk why")
	}

	return nil
}

func (u user) Get(ctx context.Context, user string) (model.User, error) {
	us := model.User{}
	err := u.qe.QueryRow(ctx, "select username, password, description from users where username = $1 ", user).
		Scan(&us.Name, &us.PasswordHash, &us.Desc)
	if err != nil {
		return model.User{}, errors.New("sorry cannot get user idk why")
	}

	return us, nil
}

func (u user) Update(ctx context.Context, user, description string) error {
	_, err := u.qe.Exec(ctx, "update users set description = $2 where username = $1", user, description)
	if err != nil {
		return errors.New("sorry cannot update user idk why")
	}

	return nil
}

func (u user) Delete(ctx context.Context, user string) error {
	_, err := u.qe.Exec(ctx, "delete from users where username = $1", user)
	if err != nil {
		return errors.New("sorry cannot delete user idk why")
	}

	return nil
}
