package service

import (
	"koshechko/internal/service/model"
	"log/slog"

	"github.com/gin-gonic/gin"
	"github.com/samber/lo"
)

type viewKoshechkoRequest struct {
	Name string `json:"Name"`
}

type viewKoshechkoResp struct {
	ID         int64    `json:"id"`
	Name       string   `json:"name"`
	Owner      string   `json:"owner"`
	Text       string   `json:"text"`
	Rank       int64    `json:"rank"`
	Score      int64    `json:"score"`
	SharedWith []string `json:"shared_with"`
}

func (s *Service) View(c *gin.Context) {
	ctx := c.Request.Context()

	req := viewKoshechkoRequest{}
	if err := c.BindJSON(&req); err != nil {
		c.AbortWithStatus(513)
		return
	}

	username := c.GetString(UsernameKey)
	isValid := c.GetBool(IsValidKey)
	if !isValid {
		c.AbortWithStatus(403)
		return
	}

	res, err := s.reg.Koshechko().Get(ctx, req.Name)
	if err != nil {
		slog.Error("reg get", err)
		c.AbortWithStatus(571)
		return
	}

	rank, err := s.lb.KoshechkoRank(ctx, req.Name)
	if err != nil {
		slog.Error("rank", err)
		c.AbortWithStatus(228)
		return
	}

	score, err := s.lb.KoshechkoScore(ctx, req.Name)
	if err != nil {
		slog.Error("rank", err)
		c.AbortWithStatus(228)
		return
	}
	if score == model.PublicKoshechko {
		c.JSON(200, viewKoshechkoResp{
			ID:         res.ID,
			Name:       res.Name,
			Owner:      res.Owner,
			Text:       res.Text,
			SharedWith: res.SharedWith,
		})
		return
	}

	if res.Owner != username && !lo.Contains(res.SharedWith, username) {
		c.AbortWithStatus(408)
		return
	}

	c.JSON(200, viewKoshechkoResp{
		ID:         res.ID,
		Name:       res.Name,
		Owner:      res.Owner,
		Text:       res.Text,
		Rank:       rank,
		Score:      score,
		SharedWith: res.SharedWith,
	})
}
