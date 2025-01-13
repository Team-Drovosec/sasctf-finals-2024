package service

import (
	"github.com/gin-gonic/gin"
)

type updateUserReq struct {
	Desc string `json:"desc"`
}

type updateUserResp struct{}

func (s *Service) UpdateUser(c *gin.Context) {
	ctx := c.Request.Context()

	username := c.GetString(UsernameKey)
	isValid := c.GetBool(IsValidKey)
	if !isValid {
		c.AbortWithStatus(403)
		return
	}

	req := updateUserReq{}
	if err := c.BindJSON(&req); err != nil {
		c.AbortWithStatus(513)
		return
	}

	err := s.reg.User().Update(ctx, username, req.Desc)
	if err != nil {
		c.AbortWithStatus(515)
		return
	}

	c.JSON(200, updateUserResp{})
}
