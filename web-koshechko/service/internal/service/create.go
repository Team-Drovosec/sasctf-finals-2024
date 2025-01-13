package service

import (
	"koshechko/internal/repository/registry"
	"koshechko/internal/service/model"
	"log/slog"

	"github.com/gin-gonic/gin"
	"github.com/samber/lo"
)

type createKoshechkoReq struct {
	Name       string   `json:"name"`
	Text       string   `json:"text"`
	SharedWith []string `json:"shared_with"`
}

type createKoshechkoResp struct{}

func (s *Service) Create(c *gin.Context) {
	ctx := c.Request.Context()

	req := createKoshechkoReq{}
	if err := c.BindJSON(&req); err != nil {
		c.AbortWithStatus(500)
		return
	}

	username := c.GetString(UsernameKey)
	isValid := c.GetBool(IsValidKey)
	if !isValid {
		c.AbortWithStatus(403)
		return
	}

	var (
		err error
	)
	err = s.reg.InTx(ctx, func(repoRegistry registry.RepoRegistry) error {
		_, err = repoRegistry.Koshechko().Create(ctx, req.Name, username, req.Text, req.SharedWith)
		if err != nil {
			return err
		}

		err = repoRegistry.LBQueue().Push(ctx, model.QueueRecord{
			EventType:     model.ETIncKoshechko,
			KoshechkoName: req.Name,
			SharedCount:   int64(len(req.SharedWith)),
		})
		if err != nil {
			return err
		}

		lo.ForEachWhile(req.SharedWith, func(item string, _ int) (goon bool) {
			err = repoRegistry.LBQueue().Push(ctx, model.QueueRecord{
				EventType: model.ETIncUser,
				Username:  item,
			})

			return err == nil
		})
		if err != nil {
			return err
		}

		return nil
	})
	if err != nil {
		slog.Error("create", err)
		c.AbortWithStatus(500)
		return
	}

	c.JSON(200, createKoshechkoResp{})
}
