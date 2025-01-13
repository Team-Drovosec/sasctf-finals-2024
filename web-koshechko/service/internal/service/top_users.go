package service

import (
	"koshechko/internal/service/model"
	"log/slog"

	"github.com/gin-gonic/gin"
	"github.com/samber/lo"
)

type topUsersResp struct {
	Top []struct {
		Username string `json:"username"`
		Rank     int64  `json:"rank"`
		Score    int64  `json:"score"`
	} `json:"top"`
}

func (s *Service) TopUsers(c *gin.Context) {
	ctx := c.Request.Context()

	top, err := s.lb.TopUsers(ctx)
	if err != nil {
		slog.Error("TopUsers:", "err", err)
		c.AbortWithStatus(567)
		return
	}

	c.JSON(200, topUsersResp{Top: []struct {
		Username string `json:"username"`
		Rank     int64  `json:"rank"`
		Score    int64  `json:"score"`
	}(lo.Map(top, func(item model.LBUser, index int) struct {
		Username string
		Rank     int64
		Score    int64
	} {
		return struct {
			Username string
			Rank     int64
			Score    int64
		}{Username: item.Username, Rank: item.Rank, Score: item.Score}
	}),
	),
	})
}
