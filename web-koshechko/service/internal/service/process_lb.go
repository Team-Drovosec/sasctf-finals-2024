package service

import (
	"context"
	"koshechko/internal/repository/registry"
	"koshechko/internal/service/model"
	"log/slog"
	"time"

	"github.com/cenkalti/backoff/v4"
	"github.com/samber/lo"
	"go.uber.org/multierr"
)

func (s *Service) Process(ctx context.Context) error {
	return s.reg.InTx(ctx, func(repoRegistry registry.RepoRegistry) error {
		recs, err := repoRegistry.LBQueue().GetN(ctx, 500)
		slog.Info("processing", "recs", recs)
		if err != nil {
			return err
		}

		for _, rec := range recs {
			bf := backoff.NewExponentialBackOff(backoff.WithMaxElapsedTime(time.Second))

			err = backoff.Retry(func() error {
				slog.Info("handle", "recs", recs)
				return s.handleRec(ctx, repoRegistry, rec)
			}, bf)
			if err != nil {
				s.reg.LBQueue().DelN(ctx, []int64{rec.Id})
				return err
			}
		}

		ids := lo.Map(recs,
			func(rec model.QueueRecord, _ int) int64 { return rec.Id },
		)
		return repoRegistry.LBQueue().DelN(ctx, ids)
	})
}

func (s *Service) handleRec(ctx context.Context, repo registry.RepoRegistry, rec model.QueueRecord) (err error) {
	switch rec.EventType {
	case model.ETIncUser:
		err = s.lb.IncUser(ctx, rec.Username)

	case model.ETIncKoshechko:
		err = s.lb.IncKoshechko(ctx, rec.KoshechkoName)

	case model.ETDelKoshechko:
		err = multierr.Append(
			repo.Koshechko().Delete(ctx, rec.KoshechkoName),
			s.lb.DelKoshechko(ctx, rec.KoshechkoName),
		)

	case model.ETDelUser:
		err = multierr.Append(
			repo.User().Delete(ctx, rec.Username),
			s.lb.DelUser(ctx, rec.Username),
		)

	case model.ETUpdateKoshechko:
		for _, sharedWith := range rec.KoshechkoSharedWith {
			s.lb.IncUser(ctx, sharedWith)
		}
		
		err = repo.Koshechko().Update(
			ctx,
			rec.KoshechkoName,
			rec.KoshechkoNewName,
			rec.KoshechkoText,
			rec.KoshechkoSharedWith,
		)
	}

	return err
}
