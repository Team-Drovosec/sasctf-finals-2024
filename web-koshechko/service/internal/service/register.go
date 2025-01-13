package service

import (
	"koshechko/internal/repository/hash"
	"log/slog"

	"github.com/gin-gonic/gin"
)

type registerReq struct {
	Username string `json:"username"`
	Password string `json:"password"`
	Desc     string `json:"desc"`
}

type registerResp struct{}

func (s *Service) Register(c *gin.Context) {
	ctx := c.Request.Context()

	req := registerReq{}
	if err := c.BindJSON(&req); err != nil {
		slog.Error("parse", "err", err)
		c.AbortWithStatus(532)
		return
	}

	hashPasswd, err := hash.Hash(req.Password)
	if err != nil {
		slog.Error("hash", "err", err)
		c.AbortWithStatus(777)
		return
	}

	if err := s.reg.User().Save(ctx, req.Username, hashPasswd, req.Desc); err != nil {
		slog.Error("save", "err", err)
		c.AbortWithStatus(514)
		return
	}

	c.JSON(200, registerResp{})
}
