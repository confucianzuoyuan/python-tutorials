CREATE DATABASE `messageboard` DEFAULT CHARACTER SET utf8;

use messageboard;

CREATE TABLE message (
    id bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    username varchar(32) NOT NULL COMMENT '姓名',
    email char(40) NOT NULL COMMENT '邮箱',
    useraddress char(100) NOT NULL COMMENT '地址',
    messagetext text NULL COMMENT '留言',
    up_utime datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    up_ctime datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id)
) ENGINE=InnoDB AUTO_INCREMENT=10000 DEFAULT CHARSET=utf8 COMMENT='留言板';