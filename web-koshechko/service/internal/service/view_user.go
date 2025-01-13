package service

import (
	"log/slog"

	"github.com/gin-gonic/gin"
)

type viewUserRequest struct {
	Name string `json:"name"`
}

type viewUserResp struct {
	Name string `json:"name"`
	Rank int64  `json:"rank"`
	Desc string `json:"text"`
}

func (s *Service) ViewUser(c *gin.Context) {
	ctx := c.Request.Context()

	req := viewUserRequest{}
	if err := c.BindJSON(&req); err != nil {
		c.AbortWithStatus(513)
		return
	}

	res, err := s.reg.User().Get(ctx, req.Name)
	if err != nil {
		slog.Error("reg get", err)
		c.AbortWithStatus(571)
		return
	}

	rank, err := s.lb.UserRank(ctx, req.Name)
	if err != nil {
		slog.Error("rank", err)
		c.AbortWithStatus(228)
		return
	}

	c.JSON(200, viewUserResp{
		Name: req.Name,
		Rank: rank,
		Desc: res.Desc,
	})
}
