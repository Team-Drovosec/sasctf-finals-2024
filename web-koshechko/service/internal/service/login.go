package service

import (
	"koshechko/internal/repository/hash"
	"log/slog"

	"github.com/gin-gonic/gin"
)

type loginReq struct {
	PasswordHash string `json:"password"`
}

type loginResp struct{}

func (s *Service) Login(c *gin.Context) {
	ctx := c.Request.Context()

	req := loginReq{}
	if err := c.BindJSON(&req); err != nil {
		slog.Error("bind", err)
		c.AbortWithStatus(418)
		return
	}

	username := c.GetString(UsernameKey)
	token := c.Request.Header.Get("token")

	tok, err := s.tok.GetToken(ctx, username)
	if err != nil {
		slog.Error("tok", err)
		c.AbortWithStatus(544)
		return
	}

	u, err := s.reg.User().Get(ctx, username)
	if err != nil {
		slog.Error("getuser", err)
		c.AbortWithStatus(523)
		return
	}

	needHash, err := hash.AddHash(string(u.PasswordHash), tok)
	if err != nil {
		c.AbortWithStatus(577)
		return
	}

	if needHash != req.PasswordHash {
		slog.Error("wrong", "need", needHash, "req", req.PasswordHash)
		_ = s.session.DeleteSession(ctx, token)
		_ = s.tok.ResetToken(ctx, username)
		c.AbortWithStatus(333)

		return
	}

	err = s.session.Auth(ctx, token)
	if err != nil {
		slog.Error("auth", err)
		c.AbortWithStatus(544)
		return
	}

	c.JSON(200, loginResp{})
}
