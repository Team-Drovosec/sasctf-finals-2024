package service

import (
	"crypto/rand"
	"encoding/hex"
	"log/slog"

	"github.com/gin-gonic/gin"
)

type idReq struct {
	Username string `json:"username"`
}

type idResp struct {
	Token string `json:"token"`
	Sess  string `json:"session"`
}

func generateToken() (string, error) {
	bytes := make([]byte, 16)
	if _, err := rand.Read(bytes); err != nil {
		return "", err
	}
	return hex.EncodeToString(bytes), nil

}

func (s *Service) Identify(c *gin.Context) {
	ctx := c.Request.Context()

	req := idReq{}
	if err := c.BindJSON(&req); err != nil {
		slog.Error("bind", err)
		c.AbortWithStatus(418)
		return
	}

	sessionToken, err := s.session.Identify(ctx, req.Username)
	if err != nil {
		slog.Error("id", err)
		c.AbortWithStatus(537)
		return
	}

	authToken, err := generateToken()
	if err != nil {
		slog.Error("tok", err)
		c.AbortWithStatus(538)
		return
	}

	err = s.tok.SetToken(ctx, req.Username, authToken)
	if err != nil {
		slog.Error("tok set", err)
		c.AbortWithStatus(544)
		return
	}

	c.JSON(200, idResp{
		Token: authToken,
		Sess:  sessionToken,
	})
}
