package lb_queue

import (
	"context"
	"errors"
	"koshechko/internal/database"
	"koshechko/internal/service/model"
)

type Repository interface {
	Push(context.Context, model.QueueRecord) error
	GetN(ctx context.Context, N int64) ([]model.QueueRecord, error)
	DelN(ctx context.Context, ids []int64) error
}

type lb_queue struct {
	qe database.QueryExecutor
}

func New(qe database.QueryExecutor) Repository {
	return lb_queue{qe: qe}
}

func (l lb_queue) Push(ctx context.Context, record model.QueueRecord) error {
	_, err := l.qe.Exec(ctx,
		"insert into lb_queue (type, username, koshechko_name, shared_count, koshechko_new_name, koshechko_text, koshechko_shared_with) values ($1, $2, $3, $4, $5, $6, $7)",
		record.EventType, record.Username, record.KoshechkoName, record.SharedCount, record.KoshechkoNewName, record.KoshechkoText, record.KoshechkoSharedWith)
	if err != nil {
		return errors.New("sorry cannot push into lb_queue idk why")
	}

	return nil
}

func (l lb_queue) GetN(ctx context.Context, N int64) ([]model.QueueRecord, error) {
	rows, err := l.qe.Query(ctx, "select id, type, username, koshechko_name, shared_count, koshechko_new_name, koshechko_text, koshechko_shared_with from lb_queue order by created_at")
	if err != nil {
		return nil, errors.New("sorry caanot get n from lb_queue idk why")
	}
	defer rows.Close()

	res := make([]model.QueueRecord, 0, N)
	for rows.Next() {
		rec := model.QueueRecord{}
		err := rows.Scan(&rec.Id, &rec.EventType, &rec.Username, &rec.KoshechkoName, &rec.SharedCount, &rec.KoshechkoNewName, &rec.KoshechkoText, &rec.KoshechkoSharedWith)
		if err != nil {
			return nil, errors.New("sorry cannot scan into lb queue rec idk why")
		}

		res = append(res, rec)
	}

	return res, nil
}

func (l lb_queue) DelN(ctx context.Context, ids []int64) error {
	_, err := l.qe.Exec(ctx, `
		delete from lb_queue where id = any($1);
	`, ids)
	if err != nil {
		return err
	}

	return nil
}
