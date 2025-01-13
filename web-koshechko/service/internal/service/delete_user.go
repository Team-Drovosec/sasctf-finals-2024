package service

import (
	"koshechko/internal/service/model"

	"github.com/gin-gonic/gin"
)

type deleteUserResp struct{}

func (s *Service) DeleteUser(c *gin.Context) {
	ctx := c.Request.Context()

	username := c.GetString(UsernameKey)
	isValid := c.GetBool(IsValidKey)
	if !isValid {
		c.AbortWithStatus(403)
		return
	}

	u, err := s.reg.User().Get(ctx, username)
	if err != nil {
		c.AbortWithStatus(505)
		return
	}

	if u.Name != username {
		c.AbortWithStatus(454)
		return
	}

	err = s.reg.LBQueue().Push(ctx, model.QueueRecord{
		EventType: model.ETDelUser,
		Username:  username,
	})
	if err != nil {
		c.AbortWithStatus(445)
		return
	}

	c.JSON(200, deleteKoshechkoResp{})
}
