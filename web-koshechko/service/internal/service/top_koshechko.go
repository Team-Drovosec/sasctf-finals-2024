package service

import (
	"koshechko/internal/service/model"
	"log/slog"

	"github.com/gin-gonic/gin"
	"github.com/samber/lo"
)

type topKoshechkoResp struct {
	Top []struct {
		Name  string `json:"name"`
		Rank  int64  `json:"rank"`
		Score int64  `json:"score"`
	} `json:"top"`
}

func (s *Service) TopKoshechko(c *gin.Context) {
	ctx := c.Request.Context()

	top, err := s.lb.TopKoshechko(ctx)
	if err != nil {
		slog.Error("TopKoshechko:", "err", err)
		c.AbortWithStatus(567)
		return
	}

	c.JSON(200, topKoshechkoResp{Top: []struct {
		Name  string `json:"name"`
		Rank  int64  `json:"rank"`
		Score int64  `json:"score"`
	}(lo.Map(top, func(item model.LBKoshechko, index int) struct {
		Name  string
		Rank  int64
		Score int64
	} {
		return struct {
			Name  string
			Rank  int64
			Score int64
		}{Name: item.Name, Rank: item.Rank, Score: item.Score}
	}),
	),
	})
}
