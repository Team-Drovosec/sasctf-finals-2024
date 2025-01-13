package service

import (
	"koshechko/internal/service/model"
	"log/slog"

	"github.com/gin-gonic/gin"
)

type deleteKosheckoReq struct {
	Name string `json:"name"`
}

type deleteKoshechkoResp struct{}

func (s *Service) DeleteKoshechko(c *gin.Context) {
	ctx := c.Request.Context()

	username := c.GetString(UsernameKey)
	isValid := c.GetBool(IsValidKey)
	if !isValid {
		c.AbortWithStatus(403)
		return
	}

	req := deleteKosheckoReq{}
	if err := c.BindJSON(&req); err != nil {
		c.AbortWithStatus(500)
		return
	}

	k, err := s.reg.Koshechko().Get(ctx, req.Name)
	if err != nil {
		c.AbortWithStatus(505)
		return
	}

	if k.Owner != username {
		slog.Error("wrong owner", "owner", k.Owner, "uname", username)
		c.AbortWithStatus(467)
		return
	}

	err = s.reg.LBQueue().Push(ctx, model.QueueRecord{
		EventType:     model.ETDelKoshechko,
		KoshechkoName: req.Name,
	})
	if err != nil {
		c.AbortWithStatus(445)
		return
	}

	c.JSON(200, deleteKoshechkoResp{})
}
