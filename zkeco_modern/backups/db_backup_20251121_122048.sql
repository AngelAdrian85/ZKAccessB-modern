-- MySQL dump 10.11
--
-- Host: localhost    Database: zkeco_db
-- ------------------------------------------------------
-- Server version	5.0.45-community-nt

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `zkeco_db`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `zkeco_db` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `zkeco_db`;

--
-- Table structure for table `acc_antiback`
--

DROP TABLE IF EXISTS `acc_antiback`;
CREATE TABLE `acc_antiback` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `device_id` int(11) default NULL,
  `one_mode` tinyint(1) NOT NULL,
  `two_mode` tinyint(1) NOT NULL,
  `three_mode` tinyint(1) NOT NULL,
  `four_mode` tinyint(1) NOT NULL,
  `five_mode` tinyint(1) NOT NULL,
  `six_mode` tinyint(1) NOT NULL,
  `seven_mode` tinyint(1) NOT NULL,
  `eight_mode` tinyint(1) NOT NULL,
  `nine_mode` tinyint(1) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `acc_antiback_device_id` (`device_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_antiback`
--

LOCK TABLES `acc_antiback` WRITE;
/*!40000 ALTER TABLE `acc_antiback` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_antiback` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_auxiliary`
--

DROP TABLE IF EXISTS `acc_auxiliary`;
CREATE TABLE `acc_auxiliary` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `device_id` int(11) default NULL,
  `aux_no` smallint(5) unsigned default NULL,
  `printer_number` varchar(30) default NULL,
  `aux_name` varchar(30) default NULL,
  `aux_state` smallint(6) default NULL,
  `time_zone_status` smallint(6) default NULL,
  `time_zone_id` int(11) default NULL,
  PRIMARY KEY  (`id`),
  KEY `acc_auxiliary_device_id` (`device_id`),
  KEY `acc_auxiliary_time_zone_id` (`time_zone_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_auxiliary`
--

LOCK TABLES `acc_auxiliary` WRITE;
/*!40000 ALTER TABLE `acc_auxiliary` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_auxiliary` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_device`
--

DROP TABLE IF EXISTS `acc_device`;
CREATE TABLE `acc_device` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `device_id` int(11) default NULL,
  `door_count` int(11) default NULL,
  `reader_count` int(11) default NULL,
  `aux_in_count` int(11) default NULL,
  `aux_out_count` int(11) default NULL,
  `machine_type` int(11) default NULL,
  `IsOnlyRFMachine` int(11) default NULL,
  `iclock_server_on` tinyint(1) NOT NULL,
  `global_apb_on` tinyint(1) NOT NULL,
  `rexinput_fun_on` tinyint(1) NOT NULL,
  `card_format_fun_on` tinyint(1) NOT NULL,
  `super_auth_fun_on` tinyint(1) NOT NULL,
  `time_apb_fun_on` tinyint(1) NOT NULL,
  `reader_cfg_fun_on` tinyint(1) NOT NULL,
  `reader_linkage_fun_on` tinyint(1) NOT NULL,
  `relay_state_fun_on` tinyint(1) NOT NULL,
  `ext_485_reader_fun_on` tinyint(1) NOT NULL,
  `ctl_all_relay_fun_on` tinyint(1) NOT NULL,
  `loss_card_fun_on` tinyint(1) NOT NULL,
  `aux_in_monitor_fun_on` tinyint(1) NOT NULL,
  `aux_out_tz_fun_on` tinyint(1) NOT NULL,
  `user_type_fun_on` tinyint(1) NOT NULL,
  `dst_fun_on` tinyint(1) NOT NULL,
  `auto_wgfmt_fun_on` tinyint(1) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `device_id` (`device_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_device`
--

LOCK TABLES `acc_device` WRITE;
/*!40000 ALTER TABLE `acc_device` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_device` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_door`
--

DROP TABLE IF EXISTS `acc_door`;
CREATE TABLE `acc_door` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `device_id` int(11) default NULL,
  `door_no` smallint(5) unsigned default NULL,
  `door_name` varchar(30) default NULL,
  `lock_delay` smallint(5) unsigned default NULL,
  `back_lock` tinyint(1) NOT NULL,
  `sensor_delay` smallint(5) unsigned default NULL,
  `opendoor_type` smallint(6) default NULL,
  `inout_state` smallint(6) default NULL,
  `lock_active_id` int(11) default NULL,
  `long_open_id` int(11) default NULL,
  `wiegand_fmt_id` int(11) default NULL,
  `card_intervaltime` smallint(5) unsigned default NULL,
  `reader_type` smallint(6) default NULL,
  `is_att` tinyint(1) NOT NULL,
  `force_pwd` varchar(18) default NULL,
  `supper_pwd` varchar(18) default NULL,
  `door_sensor_status` smallint(6) default NULL,
  `map_id` int(11) default NULL,
  `duration_apb` smallint(5) unsigned default NULL,
  `global_apb` tinyint(1) NOT NULL,
  `relay_reverse_status` smallint(6) default NULL,
  `latch_door_type` smallint(6) default NULL,
  `latch_time_out` smallint(5) unsigned default NULL,
  `enabled` tinyint(1) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `acc_door_device_id` (`device_id`),
  KEY `acc_door_lock_active_id` (`lock_active_id`),
  KEY `acc_door_long_open_id` (`long_open_id`),
  KEY `acc_door_wiegand_fmt_id` (`wiegand_fmt_id`),
  KEY `acc_door_map_id` (`map_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_door`
--

LOCK TABLES `acc_door` WRITE;
/*!40000 ALTER TABLE `acc_door` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_door` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_email`
--

DROP TABLE IF EXISTS `acc_email`;
CREATE TABLE `acc_email` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `sender` varchar(30) default NULL,
  `receiver` longtext,
  `content` longtext,
  `attachments` varchar(200) default NULL,
  `time` datetime default NULL,
  `event_type` smallint(6) default NULL,
  `send_ret` smallint(6) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_email`
--

LOCK TABLES `acc_email` WRITE;
/*!40000 ALTER TABLE `acc_email` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_email` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_firstopen`
--

DROP TABLE IF EXISTS `acc_firstopen`;
CREATE TABLE `acc_firstopen` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `door_id` int(11) default NULL,
  `timeseg_id` int(11) default NULL,
  PRIMARY KEY  (`id`),
  KEY `acc_firstopen_door_id` (`door_id`),
  KEY `acc_firstopen_timeseg_id` (`timeseg_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_firstopen`
--

LOCK TABLES `acc_firstopen` WRITE;
/*!40000 ALTER TABLE `acc_firstopen` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_firstopen` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_firstopen_emp`
--

DROP TABLE IF EXISTS `acc_firstopen_emp`;
CREATE TABLE `acc_firstopen_emp` (
  `id` int(11) NOT NULL auto_increment,
  `accfirstopen_id` int(11) NOT NULL,
  `employee_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `accfirstopen_id` (`accfirstopen_id`,`employee_id`),
  KEY `acc_firstopen_emp_accfirstopen_id` (`accfirstopen_id`),
  KEY `acc_firstopen_emp_employee_id` (`employee_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_firstopen_emp`
--

LOCK TABLES `acc_firstopen_emp` WRITE;
/*!40000 ALTER TABLE `acc_firstopen_emp` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_firstopen_emp` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_global_apb`
--

DROP TABLE IF EXISTS `acc_global_apb`;
CREATE TABLE `acc_global_apb` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `name` varchar(30) default NULL,
  `timeseg_id` int(11) default NULL,
  `group_1_id` int(11) default NULL,
  `group_2_id` int(11) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `acc_global_apb_timeseg_id` (`timeseg_id`),
  KEY `acc_global_apb_group_1_id` (`group_1_id`),
  KEY `acc_global_apb_group_2_id` (`group_2_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_global_apb`
--

LOCK TABLES `acc_global_apb` WRITE;
/*!40000 ALTER TABLE `acc_global_apb` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_global_apb` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_global_apb_group`
--

DROP TABLE IF EXISTS `acc_global_apb_group`;
CREATE TABLE `acc_global_apb_group` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `name` varchar(30) default NULL,
  `memo` varchar(70) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_global_apb_group`
--

LOCK TABLES `acc_global_apb_group` WRITE;
/*!40000 ALTER TABLE `acc_global_apb_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_global_apb_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_holidays`
--

DROP TABLE IF EXISTS `acc_holidays`;
CREATE TABLE `acc_holidays` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `holiday_name` varchar(30) default NULL,
  `holiday_type` smallint(6) default NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `loop_by_year` smallint(6) default NULL,
  `memo` varchar(70) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `holiday_name` (`holiday_name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_holidays`
--

LOCK TABLES `acc_holidays` WRITE;
/*!40000 ALTER TABLE `acc_holidays` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_holidays` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_interlock`
--

DROP TABLE IF EXISTS `acc_interlock`;
CREATE TABLE `acc_interlock` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `device_id` int(11) default NULL,
  `one_mode` tinyint(1) NOT NULL,
  `two_mode` tinyint(1) NOT NULL,
  `three_mode` tinyint(1) NOT NULL,
  `four_mode` tinyint(1) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `device_id` (`device_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_interlock`
--

LOCK TABLES `acc_interlock` WRITE;
/*!40000 ALTER TABLE `acc_interlock` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_interlock` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_levelset`
--

DROP TABLE IF EXISTS `acc_levelset`;
CREATE TABLE `acc_levelset` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `level_name` varchar(30) default NULL,
  `level_timeseg_id` int(11) default NULL,
  `level_type` int(11) default NULL,
  `is_visitor` int(11) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `level_name` (`level_name`),
  KEY `acc_levelset_level_timeseg_id` (`level_timeseg_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_levelset`
--

LOCK TABLES `acc_levelset` WRITE;
/*!40000 ALTER TABLE `acc_levelset` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_levelset` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_levelset_door_group`
--

DROP TABLE IF EXISTS `acc_levelset_door_group`;
CREATE TABLE `acc_levelset_door_group` (
  `id` int(11) NOT NULL auto_increment,
  `acclevelset_id` int(11) NOT NULL,
  `accdoor_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `acclevelset_id` (`acclevelset_id`,`accdoor_id`),
  KEY `acc_levelset_door_group_acclevelset_id` (`acclevelset_id`),
  KEY `acc_levelset_door_group_accdoor_id` (`accdoor_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_levelset_door_group`
--

LOCK TABLES `acc_levelset_door_group` WRITE;
/*!40000 ALTER TABLE `acc_levelset_door_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_levelset_door_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_levelset_emp`
--

DROP TABLE IF EXISTS `acc_levelset_emp`;
CREATE TABLE `acc_levelset_emp` (
  `id` int(11) NOT NULL auto_increment,
  `acclevelset_id` int(11) NOT NULL,
  `employee_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `acclevelset_id` (`acclevelset_id`,`employee_id`),
  KEY `acc_levelset_emp_acclevelset_id` (`acclevelset_id`),
  KEY `acc_levelset_emp_employee_id` (`employee_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_levelset_emp`
--

LOCK TABLES `acc_levelset_emp` WRITE;
/*!40000 ALTER TABLE `acc_levelset_emp` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_levelset_emp` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_linkageio`
--

DROP TABLE IF EXISTS `acc_linkageio`;
CREATE TABLE `acc_linkageio` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `linkage_name` varchar(30) NOT NULL,
  `device_id` int(11) default NULL,
  `trigger_opt` smallint(6) default NULL,
  `in_address_hide` smallint(6) default NULL,
  `in_address` smallint(6) default NULL,
  `out_type_hide` smallint(6) default NULL,
  `out_address_hide` smallint(6) default NULL,
  `out_address` smallint(6) default NULL,
  `action_type` smallint(6) default NULL,
  `delay_time` smallint(5) unsigned default NULL,
  `video_linkageio_state` varchar(10) NOT NULL,
  `video_linkageio_time` int(11) default NULL,
  `video_linkageio_record_time` int(11) default NULL,
  `email_address` longtext,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `linkage_name` (`linkage_name`),
  KEY `acc_linkageio_device_id` (`device_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_linkageio`
--

LOCK TABLES `acc_linkageio` WRITE;
/*!40000 ALTER TABLE `acc_linkageio` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_linkageio` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_map`
--

DROP TABLE IF EXISTS `acc_map`;
CREATE TABLE `acc_map` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `map_name` varchar(30) default NULL,
  `map_path` varchar(30) default NULL,
  `area_id` int(11) default NULL,
  `width` double default NULL,
  `height` double default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `map_name` (`map_name`),
  KEY `acc_map_area_id` (`area_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_map`
--

LOCK TABLES `acc_map` WRITE;
/*!40000 ALTER TABLE `acc_map` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_map` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_mapdoorpos`
--

DROP TABLE IF EXISTS `acc_mapdoorpos`;
CREATE TABLE `acc_mapdoorpos` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `map_door_id` int(11) default NULL,
  `map_id` int(11) default NULL,
  `width` double default NULL,
  `left` double default NULL,
  `top` double default NULL,
  PRIMARY KEY  (`id`),
  KEY `acc_mapdoorpos_map_door_id` (`map_door_id`),
  KEY `acc_mapdoorpos_map_id` (`map_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_mapdoorpos`
--

LOCK TABLES `acc_mapdoorpos` WRITE;
/*!40000 ALTER TABLE `acc_mapdoorpos` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_mapdoorpos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_monitor_log`
--

DROP TABLE IF EXISTS `acc_monitor_log`;
CREATE TABLE `acc_monitor_log` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `log_tag` int(11) default NULL,
  `time` datetime default NULL,
  `pin` varchar(20) default NULL,
  `card_no` varchar(20) default NULL,
  `device_id` int(11) default NULL,
  `device_sn` varchar(20) NOT NULL,
  `device_name` varchar(20) default NULL,
  `verified` int(11) default NULL,
  `state` int(11) default NULL,
  `state_name` varchar(30) default NULL,
  `event_type` smallint(6) default NULL,
  `trigger_opt` smallint(6) default NULL,
  `event_point_type` smallint(6) default NULL,
  `event_point_id` int(11) default NULL,
  `event_point_name` varchar(50) default NULL,
  `description` longtext,
  `firstname` varchar(24) default NULL,
  `lastname` varchar(20) default NULL,
  `dept` varchar(100) default NULL,
  `area` varchar(30) default NULL,
  `video_ip` varchar(40) default NULL,
  `channel_no` varchar(10) default NULL,
  `vid_record_path_name` varchar(200) default NULL,
  `vid_record_state` smallint(6) default NULL,
  `vid_capture_path_name` varchar(200) default NULL,
  `vid_capture_state` smallint(6) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `time` (`time`,`pin`,`card_no`,`device_id`,`verified`,`state`,`event_type`,`event_point_type`,`event_point_id`,`trigger_opt`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_monitor_log`
--

LOCK TABLES `acc_monitor_log` WRITE;
/*!40000 ALTER TABLE `acc_monitor_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_monitor_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_morecardempgroup`
--

DROP TABLE IF EXISTS `acc_morecardempgroup`;
CREATE TABLE `acc_morecardempgroup` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `group_name` varchar(30) NOT NULL,
  `memo` varchar(70) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `group_name` (`group_name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_morecardempgroup`
--

LOCK TABLES `acc_morecardempgroup` WRITE;
/*!40000 ALTER TABLE `acc_morecardempgroup` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_morecardempgroup` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_morecardgroup`
--

DROP TABLE IF EXISTS `acc_morecardgroup`;
CREATE TABLE `acc_morecardgroup` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `comb_id` int(11) default NULL,
  `group_id` int(11) default NULL,
  `opener_number` int(11) default NULL,
  PRIMARY KEY  (`id`),
  KEY `acc_morecardgroup_comb_id` (`comb_id`),
  KEY `acc_morecardgroup_group_id` (`group_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_morecardgroup`
--

LOCK TABLES `acc_morecardgroup` WRITE;
/*!40000 ALTER TABLE `acc_morecardgroup` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_morecardgroup` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_morecardset`
--

DROP TABLE IF EXISTS `acc_morecardset`;
CREATE TABLE `acc_morecardset` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `door_id` int(11) default NULL,
  `comb_name` varchar(30) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `comb_name` (`comb_name`),
  KEY `acc_morecardset_door_id` (`door_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_morecardset`
--

LOCK TABLES `acc_morecardset` WRITE;
/*!40000 ALTER TABLE `acc_morecardset` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_morecardset` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_reader`
--

DROP TABLE IF EXISTS `acc_reader`;
CREATE TABLE `acc_reader` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `door_id` int(11) default NULL,
  `reader_no` smallint(5) unsigned default NULL,
  `reader_name` varchar(30) default NULL,
  `reader_state` smallint(6) default NULL,
  `global_apb_group_id` int(11) default NULL,
  PRIMARY KEY  (`id`),
  KEY `acc_reader_door_id` (`door_id`),
  KEY `acc_reader_global_apb_group_id` (`global_apb_group_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_reader`
--

LOCK TABLES `acc_reader` WRITE;
/*!40000 ALTER TABLE `acc_reader` DISABLE KEYS */;
/*!40000 ALTER TABLE `acc_reader` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_timeseg`
--

DROP TABLE IF EXISTS `acc_timeseg`;
CREATE TABLE `acc_timeseg` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `timeseg_name` varchar(30) NOT NULL,
  `memo` varchar(70) default NULL,
  `sunday_start1` time NOT NULL,
  `sunday_end1` time NOT NULL,
  `sunday_start2` time NOT NULL,
  `sunday_end2` time NOT NULL,
  `sunday_start3` time NOT NULL,
  `sunday_end3` time NOT NULL,
  `monday_start1` time NOT NULL,
  `monday_end1` time NOT NULL,
  `monday_start2` time NOT NULL,
  `monday_end2` time NOT NULL,
  `monday_start3` time NOT NULL,
  `monday_end3` time NOT NULL,
  `tuesday_start1` time NOT NULL,
  `tuesday_end1` time NOT NULL,
  `tuesday_start2` time NOT NULL,
  `tuesday_end2` time NOT NULL,
  `tuesday_start3` time NOT NULL,
  `tuesday_end3` time NOT NULL,
  `wednesday_start1` time NOT NULL,
  `wednesday_end1` time NOT NULL,
  `wednesday_start2` time NOT NULL,
  `wednesday_end2` time NOT NULL,
  `wednesday_start3` time NOT NULL,
  `wednesday_end3` time NOT NULL,
  `thursday_start1` time NOT NULL,
  `thursday_end1` time NOT NULL,
  `thursday_start2` time NOT NULL,
  `thursday_end2` time NOT NULL,
  `thursday_start3` time NOT NULL,
  `thursday_end3` time NOT NULL,
  `friday_start1` time NOT NULL,
  `friday_end1` time NOT NULL,
  `friday_start2` time NOT NULL,
  `friday_end2` time NOT NULL,
  `friday_start3` time NOT NULL,
  `friday_end3` time NOT NULL,
  `saturday_start1` time NOT NULL,
  `saturday_end1` time NOT NULL,
  `saturday_start2` time NOT NULL,
  `saturday_end2` time NOT NULL,
  `saturday_start3` time NOT NULL,
  `saturday_end3` time NOT NULL,
  `holidaytype1_start1` time NOT NULL,
  `holidaytype1_end1` time NOT NULL,
  `holidaytype1_start2` time NOT NULL,
  `holidaytype1_end2` time NOT NULL,
  `holidaytype1_start3` time NOT NULL,
  `holidaytype1_end3` time NOT NULL,
  `holidaytype2_start1` time NOT NULL,
  `holidaytype2_end1` time NOT NULL,
  `holidaytype2_start2` time NOT NULL,
  `holidaytype2_end2` time NOT NULL,
  `holidaytype2_start3` time NOT NULL,
  `holidaytype2_end3` time NOT NULL,
  `holidaytype3_start1` time NOT NULL,
  `holidaytype3_end1` time NOT NULL,
  `holidaytype3_start2` time NOT NULL,
  `holidaytype3_end2` time NOT NULL,
  `holidaytype3_start3` time NOT NULL,
  `holidaytype3_end3` time NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `timeseg_name` (`timeseg_name`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_timeseg`
--

LOCK TABLES `acc_timeseg` WRITE;
/*!40000 ALTER TABLE `acc_timeseg` DISABLE KEYS */;
INSERT INTO `acc_timeseg` VALUES (1,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'24-Hour Accessible','24-Hour Accessible','00:00:00','23:59:00','00:00:00','00:00:00','00:00:00','00:00:00','00:00:00','23:59:00','00:00:00','00:00:00','00:00:00','00:00:00','00:00:00','23:59:00','00:00:00','00:00:00','00:00:00','00:00:00','00:00:00','23:59:00','00:00:00','00:00:00','00:00:00','00:00:00','00:00:00','23:59:00','00:00:00','00:00:00','00:00:00','00:00:00','00:00:00','23:59:00','00:00:00','00:00:00','00:00:00','00:00:00','00:00:00','23:59:00','00:00:00','00:00:00','00:00:00','00:00:00','00:00:00','23:59:00','00:00:00','00:00:00','00:00:00','00:00:00','00:00:00','23:59:00','00:00:00','00:00:00','00:00:00','00:00:00','00:00:00','23:59:00','00:00:00','00:00:00','00:00:00','00:00:00');
/*!40000 ALTER TABLE `acc_timeseg` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acc_wiegandfmt`
--

DROP TABLE IF EXISTS `acc_wiegandfmt`;
CREATE TABLE `acc_wiegandfmt` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `wiegand_name` varchar(30) NOT NULL,
  `wiegand_count` int(11) default NULL,
  `wiegand_mode` smallint(6) NOT NULL,
  `odd_parity_start` smallint(6) default NULL,
  `odd_parity_count` smallint(6) default NULL,
  `even_parity_start` smallint(6) default NULL,
  `even_parity_count` smallint(6) default NULL,
  `cid_start` smallint(6) default NULL,
  `cid_count` smallint(6) default NULL,
  `facility_code_start` smallint(6) default NULL,
  `facility_code_count` smallint(6) default NULL,
  `site_code_start` smallint(6) default NULL,
  `site_code_count` smallint(6) default NULL,
  `manufactory_code_start` smallint(6) default NULL,
  `manufactory_code_count` smallint(6) default NULL,
  `first_p` smallint(6) default NULL,
  `second_p` smallint(6) default NULL,
  `before_fmt` varchar(80) default NULL,
  `after_fmt` varchar(80) default NULL,
  `default_fmt` tinyint(1) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=12 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `acc_wiegandfmt`
--

LOCK TABLES `acc_wiegandfmt` WRITE;
/*!40000 ALTER TABLE `acc_wiegandfmt` DISABLE KEYS */;
INSERT INTO `acc_wiegandfmt` VALUES (1,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'Auto',NULL,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'','',0),(2,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'Wiegand 26',26,1,14,13,1,13,2,24,0,0,0,0,0,0,1,26,'pccccccccccccccccccccccccp','eeeeeeeeeeeeeooooooooooooo',1),(3,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'Wiegand 26a',26,1,14,13,1,13,10,16,2,8,0,0,0,0,1,26,'pffffffffccccccccccccccccp','eeeeeeeeeeeeeooooooooooooo',0),(4,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'Wiegand 34',34,1,18,17,1,17,2,32,0,0,0,0,0,0,1,34,'pccccccccccccccccccccccccccccccccp','eeeeeeeeeeeeeeeeeooooooooooooooooo',1),(5,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'Wiegand 34a',34,1,18,17,1,17,18,16,0,0,2,16,0,0,1,34,'pssssssssssssssssccccccccccccccccp','eeeeeeeeeeeeeeeeeooooooooooooooooo',0),(6,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'Wiegand 36',36,1,1,15,16,21,18,18,0,0,2,16,0,0,1,36,'pssssssssssssssssccccccccccccccccccp','oooooooooooooooeeeeeeeeeeeeeeeeeeeee',1),(7,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'Wiegand 37',37,1,19,19,1,18,21,16,5,10,15,6,2,3,1,37,'pmmmffffffffffssssssccccccccccccccccp','eeeeeeeeeeeeeeeeeeooooooooooooooooooo',1),(8,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'Wiegand 37a',37,1,19,19,1,18,18,19,0,0,6,12,2,4,1,37,'pmmmmsssssssssssscccccccccccccccccccp','eeeeeeeeeeeeeeeeeeooooooooooooooooooo',0),(9,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'Wiegand 50',50,1,26,25,1,25,18,32,0,0,2,16,0,0,1,50,'pssssssssssssssssccccccccccccccccccccccccccccccccp','eeeeeeeeeeeeeeeeeeeeeeeeeooooooooooooooooooooooooo',1),(10,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'Wiegand 66',66,1,34,33,1,33,2,64,0,0,0,0,0,0,1,66,'pccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccp','eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeooooooooooooooooooooooooooooooooo',1),(11,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'Wiegand 35',35,1,19,17,1,18,15,20,0,0,2,13,0,0,1,35,'psssssssssssssccccccccccccccccccccp','eeeeeeeeeeeeeeeeeeooooooooooooooooo',1);
/*!40000 ALTER TABLE `acc_wiegandfmt` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `action_log`
--

DROP TABLE IF EXISTS `action_log`;
CREATE TABLE `action_log` (
  `id` int(11) NOT NULL auto_increment,
  `action_time` datetime NOT NULL,
  `user_id` int(11) default NULL,
  `content_type_id` int(11) default NULL,
  `object_id` varchar(100) default NULL,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` varchar(512) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `action_log_user_id` (`user_id`),
  KEY `action_log_content_type_id` (`content_type_id`)
) ENGINE=MyISAM AUTO_INCREMENT=94 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `action_log`
--

LOCK TABLES `action_log` WRITE;
/*!40000 ALTER TABLE `action_log` DISABLE KEYS */;
INSERT INTO `action_log` VALUES (1,'2025-10-06 15:12:43',NULL,15,'1','company(Company Name)',1,''),(2,'2025-10-06 15:12:43',NULL,15,'2','dbversion(5.31)',1,''),(3,'2025-10-06 15:12:43',NULL,15,'3','date_format(%m/%d/%Y)',1,''),(4,'2025-10-06 15:12:43',NULL,15,'4','browse_title(Access Control System)',1,''),(5,'2025-10-06 15:12:43',NULL,13,'1','System.Date Format',1,''),(6,'2025-10-06 15:12:43',NULL,13,'2','System.Time Format',1,''),(7,'2025-10-06 15:12:43',NULL,13,'3','System.Datetime Format',1,''),(8,'2025-10-06 15:12:43',NULL,13,'4','System.Shortdate format',1,''),(9,'2025-10-06 15:12:43',NULL,13,'5','System.Shortdatetime Format',1,''),(10,'2025-10-06 15:12:43',NULL,13,'6','System.Language',1,''),(11,'2025-10-06 15:12:43',NULL,13,'7','System.System Default Page',1,''),(12,'2025-10-06 15:12:43',NULL,13,'8','System.System Default Page',1,''),(13,'2025-10-06 15:12:43',NULL,13,'9','System.Device List Page',1,''),(14,'2025-10-06 15:12:43',NULL,13,'10','System.Backup Time',1,''),(15,'2025-10-06 15:12:43',NULL,13,'11','dbapp.Maximum Image Width',1,''),(16,'2025-10-06 15:12:43',NULL,13,'12','dbapp.Style',1,''),(17,'2025-10-06 15:12:43',NULL,22,'1','1 Area Name',1,''),(18,'2025-10-06 15:12:43',NULL,26,'1','01 VIP card',1,''),(19,'2025-10-06 15:12:43',NULL,26,'2','02 Ordinary card',1,''),(20,'2025-10-06 15:12:43',NULL,20,'1','1 Department Name',1,''),(21,'2025-10-06 15:12:43',NULL,54,'CompanyLogo','CompanyLogo',1,''),(22,'2025-10-06 15:12:43',NULL,13,'13','Personnel.Default access control page',1,''),(23,'2025-10-06 15:12:43',NULL,29,'1','System',1,''),(24,'2025-10-06 15:12:43',NULL,29,'2','Attendance',1,''),(25,'2025-10-06 15:12:43',NULL,29,'3','Access Control',1,''),(26,'2025-10-06 15:12:43',NULL,29,'4','Personnel',1,''),(27,'2025-10-06 15:12:44',NULL,13,'14','Device.Default access control page',1,''),(28,'2025-10-06 15:12:44',NULL,45,'1','New Year’s Day',1,''),(29,'2025-10-06 15:12:44',NULL,45,'2','National Day',1,''),(30,'2025-10-06 15:12:44',NULL,51,'1','Sick',1,''),(31,'2025-10-06 15:12:44',NULL,51,'2','Personal',1,''),(32,'2025-10-06 15:12:44',NULL,51,'3','Maternity',1,''),(33,'2025-10-06 15:12:44',NULL,51,'4','Compassionate',1,''),(34,'2025-10-06 15:12:44',NULL,51,'5','Annual',1,''),(35,'2025-10-06 15:12:44',NULL,51,'6','Business Trip',1,''),(36,'2025-10-06 15:12:44',NULL,53,'1000','LeaveClass1 object',1,''),(37,'2025-10-06 15:12:44',NULL,53,'1001','LeaveClass1 object',1,''),(38,'2025-10-06 15:12:44',NULL,53,'1002','LeaveClass1 object',1,''),(39,'2025-10-06 15:12:44',NULL,53,'1003','LeaveClass1 object',1,''),(40,'2025-10-06 15:12:44',NULL,53,'1004','LeaveClass1 object',1,''),(41,'2025-10-06 15:12:44',NULL,53,'1005','LeaveClass1 object',1,''),(42,'2025-10-06 15:12:44',NULL,53,'1008','LeaveClass1 object',1,''),(43,'2025-10-06 15:12:44',NULL,53,'1009','LeaveClass1 object',1,''),(44,'2025-10-06 15:12:44',NULL,47,'1','Flexible shift',1,''),(45,'2025-10-06 15:12:44',NULL,46,'1','Flexible TimeTable',1,''),(46,'2025-10-06 15:12:44',NULL,48,'1','Flexible shift,Flexible TimeTable',1,''),(47,'2025-10-06 15:12:44',NULL,48,'2','Flexible shift,Flexible TimeTable',1,''),(48,'2025-10-06 15:12:44',NULL,48,'3','Flexible shift,Flexible TimeTable',1,''),(49,'2025-10-06 15:12:44',NULL,48,'4','Flexible shift,Flexible TimeTable',1,''),(50,'2025-10-06 15:12:44',NULL,48,'5','Flexible shift,Flexible TimeTable',1,''),(51,'2025-10-06 15:12:44',NULL,48,'6','Flexible shift,Flexible TimeTable',1,''),(52,'2025-10-06 15:12:44',NULL,48,'7','Flexible shift,Flexible TimeTable',1,''),(53,'2025-10-06 15:12:44',NULL,13,'15','Attendance.default access control page',1,''),(54,'2025-10-06 15:12:44',NULL,65,'1','24-Hour Accessible',1,''),(55,'2025-10-06 15:12:44',NULL,67,'1','Auto',1,''),(56,'2025-10-06 15:12:44',NULL,67,'2','Wiegand 26',1,''),(57,'2025-10-06 15:12:44',NULL,67,'3','Wiegand 26a',1,''),(58,'2025-10-06 15:12:44',NULL,67,'4','Wiegand 34',1,''),(59,'2025-10-06 15:12:44',NULL,67,'5','Wiegand 34a',1,''),(60,'2025-10-06 15:12:44',NULL,67,'6','Wiegand 36',1,''),(61,'2025-10-06 15:12:44',NULL,67,'7','Wiegand 37',1,''),(62,'2025-10-06 15:12:44',NULL,67,'8','Wiegand 37a',1,''),(63,'2025-10-06 15:12:44',NULL,67,'9','Wiegand 50',1,''),(64,'2025-10-06 15:12:44',NULL,67,'10','Wiegand 66',1,''),(65,'2025-10-06 15:12:44',NULL,67,'11','Wiegand 35',1,''),(66,'2025-10-06 15:12:45',NULL,13,'16','Access Control System.default access control page',1,''),(67,'2025-10-06 15:12:45',NULL,13,'17','elevator.Default Page of Elevator Control System',1,''),(68,'2025-10-06 15:12:45',NULL,13,'18','video.Default page of Video',1,''),(69,'2025-10-06 15:12:45',NULL,13,'19','visitor.Visitors default Page',1,''),(70,'2025-10-06 15:14:13',1,NULL,'1','',5,''),(71,'2025-10-06 15:14:14',1,9,'1','[en] content type.app_label: worktable -> worktable',1,''),(72,'2025-10-06 15:14:14',1,9,'2','[en] content type.app_label: dbapp -> dbapp',1,''),(73,'2025-10-06 15:14:14',1,9,'3','[en] content type.app_label: auth -> auth',1,''),(74,'2025-10-06 15:14:14',1,9,'4','[en] content type.app_label: django_extensions -> django_extensions',1,''),(75,'2025-10-06 15:14:55',1,4,'1','admin',2,''),(76,'2025-10-06 15:15:05',1,NULL,'1','',5,''),(77,'2025-10-06 15:15:08',1,9,'5','[en] Basic code table.display: Simplified Chinese -> Simplified Chinese',1,''),(78,'2025-10-06 15:15:08',1,9,'6','[en] Basic code table.display: English -> English',1,''),(79,'2025-10-06 15:15:08',1,9,'7','[en] Basic code table.display: Spanish -> Spanish',1,''),(80,'2025-10-06 15:15:08',1,9,'8','[en] Basic code table.display: Traditional Chinese -> Traditional Chinese',1,''),(81,'2025-10-06 15:15:08',1,9,'9','[en] Basic code table.display: Polish -> Polish',1,''),(82,'2025-10-06 15:15:08',1,9,'10','[en] Basic code table.display: French -> French',1,''),(83,'2025-10-06 15:15:08',1,9,'11','[en] Basic code table.display: Arabic -> Arabic',1,''),(84,'2025-10-06 15:15:08',1,9,'12','[en] Basic code table.display: Vietnamese -> Vietnamese',1,''),(85,'2025-10-06 15:15:08',1,9,'13','[en] Basic code table.display: Thai -> Thai',1,''),(86,'2025-10-06 15:15:08',1,9,'14','[en] Basic code table.display: Russian -> Russian',1,''),(87,'2025-10-06 15:15:08',1,9,'15','[en] Basic code table.display: Portuguese -> Portuguese',1,''),(88,'2025-10-06 15:15:08',1,9,'16','[en] Basic code table.display: Italian -> Italian',1,''),(89,'2025-10-10 08:01:32',1,NULL,'1','',5,''),(90,'2025-10-14 12:47:54',1,NULL,'1','',5,''),(91,'2025-10-16 14:57:32',1,NULL,'1','',5,''),(92,'2025-10-17 08:38:39',1,NULL,'1','',5,''),(93,'2025-10-20 09:29:39',1,NULL,'1','',5,'');
/*!40000 ALTER TABLE `action_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `areaadmin`
--

DROP TABLE IF EXISTS `areaadmin`;
CREATE TABLE `areaadmin` (
  `id` int(11) NOT NULL auto_increment,
  `user_id` int(11) NOT NULL,
  `area_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `areaadmin_user_id` (`user_id`),
  KEY `areaadmin_area_id` (`area_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `areaadmin`
--

LOCK TABLES `areaadmin` WRITE;
/*!40000 ALTER TABLE `areaadmin` DISABLE KEYS */;
/*!40000 ALTER TABLE `areaadmin` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `att_attreport`
--

DROP TABLE IF EXISTS `att_attreport`;
CREATE TABLE `att_attreport` (
  `ItemName` varchar(100) NOT NULL,
  `ItemType` varchar(20) default NULL,
  `Author_id` int(11) NOT NULL,
  `ItemValue` longtext,
  `Published` smallint(6) default NULL,
  PRIMARY KEY  (`ItemName`),
  KEY `att_attreport_Author_id` (`Author_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `att_attreport`
--

LOCK TABLES `att_attreport` WRITE;
/*!40000 ALTER TABLE `att_attreport` DISABLE KEYS */;
/*!40000 ALTER TABLE `att_attreport` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `att_overtime`
--

DROP TABLE IF EXISTS `att_overtime`;
CREATE TABLE `att_overtime` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `emp_id` int(11) NOT NULL,
  `starttime` datetime NOT NULL,
  `endtime` datetime NOT NULL,
  `remark` varchar(200) default NULL,
  `audit_status` int(11) NOT NULL,
  `auditreason` varchar(100) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `emp_id` (`emp_id`,`starttime`,`endtime`),
  KEY `att_overtime_emp_id` (`emp_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `att_overtime`
--

LOCK TABLES `att_overtime` WRITE;
/*!40000 ALTER TABLE `att_overtime` DISABLE KEYS */;
/*!40000 ALTER TABLE `att_overtime` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `att_waitforprocessdata`
--

DROP TABLE IF EXISTS `att_waitforprocessdata`;
CREATE TABLE `att_waitforprocessdata` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `UserID_id` int(11) NOT NULL,
  `starttime` datetime NOT NULL,
  `endtime` datetime NOT NULL,
  `flag` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `att_waitforprocessdata_UserID_id` (`UserID_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `att_waitforprocessdata`
--

LOCK TABLES `att_waitforprocessdata` WRITE;
/*!40000 ALTER TABLE `att_waitforprocessdata` DISABLE KEYS */;
/*!40000 ALTER TABLE `att_waitforprocessdata` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `attcalclog`
--

DROP TABLE IF EXISTS `attcalclog`;
CREATE TABLE `attcalclog` (
  `id` int(11) NOT NULL auto_increment,
  `DeptID` int(11) default NULL,
  `UserId` int(11) NOT NULL,
  `StartDate` datetime default NULL,
  `EndDate` datetime NOT NULL,
  `OperTime` datetime NOT NULL,
  `Type` int(11) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `attcalclog`
--

LOCK TABLES `attcalclog` WRITE;
/*!40000 ALTER TABLE `attcalclog` DISABLE KEYS */;
/*!40000 ALTER TABLE `attcalclog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `attexception`
--

DROP TABLE IF EXISTS `attexception`;
CREATE TABLE `attexception` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `UserId` int(11) NOT NULL,
  `StartTime` datetime NOT NULL,
  `EndTime` datetime NOT NULL,
  `ExceptionID` int(11) default NULL,
  `AuditExcID` int(11) default NULL,
  `OldAuditExcID` int(11) default NULL,
  `OverlapTime` int(11) default NULL,
  `TimeLong` int(11) default NULL,
  `InScopeTime` int(11) default NULL,
  `AttDate` datetime default NULL,
  `OverlapWorkDayTail` int(11) NOT NULL,
  `OverlapWorkDay` double default NULL,
  `schindex` int(11) default NULL,
  `Minsworkday` int(11) default NULL,
  `Minsworkday1` int(11) default NULL,
  `schid` int(11) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `UserId` (`UserId`,`AttDate`,`StartTime`),
  KEY `attexception_UserId` (`UserId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `attexception`
--

LOCK TABLES `attexception` WRITE;
/*!40000 ALTER TABLE `attexception` DISABLE KEYS */;
/*!40000 ALTER TABLE `attexception` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `attparam`
--

DROP TABLE IF EXISTS `attparam`;
CREATE TABLE `attparam` (
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `ParaName` varchar(20) NOT NULL,
  `ParaType` varchar(2) default NULL,
  `ParaValue` varchar(100) NOT NULL,
  PRIMARY KEY  (`ParaName`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `attparam`
--

LOCK TABLES `attparam` WRITE;
/*!40000 ALTER TABLE `attparam` DISABLE KEYS */;
INSERT INTO `attparam` VALUES (NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'CompanyLogo',NULL,'Department Name');
/*!40000 ALTER TABLE `attparam` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `attrecabnormite`
--

DROP TABLE IF EXISTS `attrecabnormite`;
CREATE TABLE `attrecabnormite` (
  `id` int(11) NOT NULL auto_increment,
  `userid` int(11) NOT NULL,
  `checktime` datetime NOT NULL,
  `CheckType` varchar(5) NOT NULL,
  `NewType` varchar(2) default NULL,
  `AbNormiteID` int(11) default NULL,
  `SchID` int(11) default NULL,
  `OP` int(11) default NULL,
  `AttDate` datetime default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `userid` (`userid`,`AttDate`,`checktime`),
  KEY `attrecabnormite_userid` (`userid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `attrecabnormite`
--

LOCK TABLES `attrecabnormite` WRITE;
/*!40000 ALTER TABLE `attrecabnormite` DISABLE KEYS */;
/*!40000 ALTER TABLE `attrecabnormite` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `attshifts`
--

DROP TABLE IF EXISTS `attshifts`;
CREATE TABLE `attshifts` (
  `id` int(11) NOT NULL auto_increment,
  `userid` int(11) NOT NULL,
  `SchIndex` int(11) default NULL,
  `AutoSch` smallint(6) default NULL,
  `AttDate` datetime NOT NULL,
  `SchId` int(11) default NULL,
  `ClockInTime` datetime NOT NULL,
  `ClockOutTime` datetime NOT NULL,
  `StartTime` datetime default NULL,
  `EndTime` datetime default NULL,
  `WorkDay` double default NULL,
  `RealWorkDay` double default NULL,
  `NoIn` smallint(6) default NULL,
  `NoOut` smallint(6) default NULL,
  `Late` double default NULL,
  `Early` double default NULL,
  `Absent` double default NULL,
  `OverTime` double default NULL,
  `WorkTime` int(11) default NULL,
  `ExceptionID` int(11) default NULL,
  `Symbol` varchar(50) default NULL,
  `MustIn` smallint(6) default NULL,
  `MustOut` smallint(6) default NULL,
  `OverTime1` int(11) default NULL,
  `WorkMins` int(11) default NULL,
  `SSpeDayNormal` double default NULL,
  `SSpeDayWeekend` double default NULL,
  `SSpeDayHoliday` double default NULL,
  `AttTime` int(11) default NULL,
  `SSpeDayNormalOT` double default NULL,
  `SSpeDayWeekendOT` double default NULL,
  `SSpeDayHolidayOT` double default NULL,
  `AbsentMins` int(11) default NULL,
  `AttChkTime` varchar(10) default NULL,
  `AbsentR` double default NULL,
  `ScheduleName` varchar(20) default NULL,
  `IsConfirm` smallint(6) default NULL,
  `IsRead` smallint(6) default NULL,
  `Exception` varchar(100) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `userid` (`userid`,`AttDate`,`SchId`,`StartTime`),
  KEY `attshifts_userid` (`userid`),
  KEY `attshifts_SchId` (`SchId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `attshifts`
--

LOCK TABLES `attshifts` WRITE;
/*!40000 ALTER TABLE `attshifts` DISABLE KEYS */;
/*!40000 ALTER TABLE `attshifts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL auto_increment,
  `name` varchar(80) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
INSERT INTO `auth_group` VALUES (1,'role_for_employee');
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL auto_increment,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `group_id` (`group_id`,`permission_id`),
  KEY `auth_group_permissions_group_id` (`group_id`),
  KEY `auth_group_permissions_permission_id` (`permission_id`)
) ENGINE=MyISAM AUTO_INCREMENT=2755 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
INSERT INTO `auth_group_permissions` VALUES (2754,1,321),(2753,1,357),(2752,1,356),(2751,1,353),(2750,1,352),(2749,1,194),(2748,1,198),(2747,1,197),(2746,1,196),(2745,1,195),(2744,1,578),(2743,1,577),(2742,1,576),(2741,1,575),(2740,1,318),(2739,1,317),(2738,1,315),(2737,1,314),(2736,1,311),(2735,1,310),(2734,1,307),(2733,1,306),(2732,1,305),(2731,1,304),(2730,1,303),(2729,1,302),(2728,1,300),(2727,1,299),(2726,1,193),(2725,1,287),(2724,1,322),(2723,1,266),(2722,1,392),(2721,1,391);
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_message`
--

DROP TABLE IF EXISTS `auth_message`;
CREATE TABLE `auth_message` (
  `id` int(11) NOT NULL auto_increment,
  `user_id` int(11) NOT NULL,
  `message` longtext NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `auth_message_user_id` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `auth_message`
--

LOCK TABLES `auth_message` WRITE;
/*!40000 ALTER TABLE `auth_message` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_message` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL auto_increment,
  `name` varchar(50) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `content_type_id` (`content_type_id`,`codename`),
  KEY `auth_permission_content_type_id` (`content_type_id`)
) ENGINE=MyISAM AUTO_INCREMENT=589 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'浏览会话',1,'browse_session'),(2,'Can add session',1,'add_session'),(3,'Can change session',1,'change_session'),(4,'Can delete session',1,'delete_session'),(5,'浏览content type',6,'browse_contenttype'),(6,'浏览角色',3,'browse_group'),(7,'删除',3,'groupdel_group'),(8,'浏览message',5,'browse_message'),(9,'浏览权限',2,'browse_permission'),(10,'浏览用户',4,'browse_user'),(11,'删除',4,'delete_user'),(12,'Can add permission',2,'add_permission'),(13,'Can change permission',2,'change_permission'),(14,'Can delete permission',2,'delete_permission'),(15,'Can add 角色',3,'add_group'),(16,'Can change 角色',3,'change_group'),(17,'Can delete 角色',3,'delete_group'),(18,'Can add 用户',4,'add_user'),(19,'Can change 用户',4,'change_user'),(20,'Can add message',5,'add_message'),(21,'Can change message',5,'change_message'),(22,'Can delete message',5,'delete_message'),(23,'Can add content type',6,'add_contenttype'),(24,'Can change content type',6,'change_contenttype'),(25,'Can delete content type',6,'delete_contenttype'),(26,'浏览系统参数',15,'browse_appoption'),(27,'新增',15,'add_appoption'),(28,'修改',15,'change_appoption'),(29,'清空记录',15,'clear_appoption'),(30,'删除',15,'delete_appoption'),(31,'导出',15,'dataexport_appoption'),(32,'浏览基础代码表',12,'browse_basecode'),(33,'新增',12,'add_basecode'),(34,'修改',12,'change_basecode'),(35,'删除',12,'delete_basecode'),(36,'导出',12,'dataexport_basecode'),(37,'浏览翻译为数据',9,'browse_datatranslation'),(38,'新增',9,'add_datatranslation'),(39,'修改',9,'change_datatranslation'),(40,'删除',9,'delete_datatranslation'),(41,'导出',9,'dataexport_datatranslation'),(42,'浏览日志记录',7,'browse_logentry'),(43,'导出',7,'dataexport_logentry'),(44,'浏览个性设置',13,'browse_option'),(45,'新增',13,'add_option'),(46,'修改',13,'change_option'),(47,'删除',13,'delete_option'),(48,'导出',13,'dataexport_option'),(49,'浏览个人选项',16,'browse_personaloption'),(50,'新增',16,'add_personaloption'),(51,'修改',16,'change_personaloption'),(52,'删除',16,'delete_personaloption'),(53,'导出',16,'dataexport_personaloption'),(54,'浏览str resource',11,'browse_strresource'),(55,'新增',11,'add_strresource'),(56,'修改',11,'change_strresource'),(57,'删除',11,'delete_strresource'),(58,'导出',11,'dataexport_strresource'),(59,'浏览翻译为字符串资源',10,'browse_strtranslation'),(60,'新增',10,'add_strtranslation'),(61,'修改',10,'change_strtranslation'),(62,'删除',10,'delete_strtranslation'),(63,'导出',10,'dataexport_strtranslation'),(64,'浏览系统参数',14,'browse_systemoption'),(65,'新增',14,'add_systemoption'),(66,'修改',14,'change_systemoption'),(67,'删除',14,'delete_systemoption'),(68,'导出',14,'dataexport_systemoption'),(69,'Can add 日志记录',7,'add_logentry'),(70,'Can change 日志记录',7,'change_logentry'),(71,'Can delete 日志记录',7,'delete_logentry'),(72,'Can add 增加的数据',8,'add_additiondata'),(73,'Can change 增加的数据',8,'change_additiondata'),(74,'Can delete 增加的数据',8,'delete_additiondata'),(75,'Can add 用户指纹',17,'add_operatortemplate'),(76,'Can change 用户指纹',17,'change_operatortemplate'),(77,'Can delete 用户指纹',17,'delete_operatortemplate'),(78,'浏览数据库管理',18,'browse_dbbackuplog'),(79,'备份数据库',18,'opbackupdb_dbbackuplog'),(80,'初始化数据库',18,'opinitdb_dbbackuplog'),(81,'还原数据库',18,'oprestoredb_dbbackuplog'),(82,'新增',18,'add_dbbackuplog'),(83,'修改',18,'change_dbbackuplog'),(84,'删除',18,'delete_dbbackuplog'),(85,'导出',18,'dataexport_dbbackuplog'),(86,'还原数据库',6,'can_Restore_db'),(87,'浏览view model',19,'browse_viewmodel'),(88,'新增',19,'add_viewmodel'),(89,'修改',19,'change_viewmodel'),(90,'删除',19,'delete_viewmodel'),(91,'导出',19,'dataexport_viewmodel'),(92,'系统参数设置',6,'can_sys_option'),(93,'个性设置',6,'can_user_option'),(94,'浏览多卡开门人员组',21,'browse_accmorecardempgroup'),(95,'添加人员',21,'opaddemptomcegroup_accmorecardempgroup'),(96,'删除人员',21,'opdelempfrommcegroup_accmorecardempgroup'),(97,'新增',21,'add_accmorecardempgroup'),(98,'修改',21,'change_accmorecardempgroup'),(99,'删除',21,'delete_accmorecardempgroup'),(100,'导出',21,'dataexport_accmorecardempgroup'),(101,'浏览区域设置',22,'browse_area'),(102,'为区域添加人员',22,'opadjustarea_area'),(103,'同步所有区域信息到分控',22,'opsyncallareatobranch_area'),(104,'同步区域信息到分控',22,'opsynconeareatobranch_area'),(105,'新增',22,'add_area'),(106,'修改',22,'change_area'),(107,'撤消区域',22,'delete_area'),(108,'导出',22,'dataexport_area'),(109,'浏览卡类型',26,'browse_cardtype'),(110,'新增',26,'add_cardtype'),(111,'修改',26,'change_cardtype'),(112,'删除',26,'delete_cardtype'),(113,'导出',26,'dataexport_cardtype'),(114,'浏览部门',20,'browse_department'),(115,'同步所有部门信息到分控',20,'opsyncalldepttobranch_department'),(116,'同步部门信息到分控',20,'opsynconedepttobranch_department'),(117,'新增',20,'add_department'),(118,'修改',20,'change_department'),(119,'撤消',20,'delete_department'),(120,'导出',20,'dataexport_department'),(121,'导入',20,'dataimport_department'),(122,'浏览人员调动',28,'browse_empchange'),(123,'立即生效',28,'opavailable_empchange'),(124,'新增',28,'add_empchange'),(125,'修改',28,'change_empchange'),(126,'',28,'delete_empchange'),(127,'导出',28,'dataexport_empchange'),(128,'浏览人事报表',24,'browse_empitemdefine'),(129,'部门花名册',24,'deptrosterreport_empitemdefine'),(130,'人员卡片清单',24,'empcardreport_empitemdefine'),(131,'学历构成分析表',24,'empeducationreport_empitemdefine'),(132,'人员流动表',24,'empflowreport_empitemdefine'),(133,'导出',24,'dataexport_empitemdefine'),(134,'浏览人员',23,'browse_employee'),(135,'添加所属权限组',23,'opaddleveltoemp_employee'),(136,'调整区域',23,'opadjustarea_employee'),(137,'调整部门',23,'opadjustdept_employee'),(138,'制卡',23,'opcardprinting_employee'),(139,'删除所属权限组',23,'opdellevelfromemp_employee'),(140,'员工转正',23,'opemptype_employee'),(141,'人员发卡',23,'opissuecard_employee'),(142,'离职',23,'opleave_employee'),(143,'挂失卡',23,'oplosecard_employee'),(144,'登记指纹',23,'opregisterfinger_employee'),(145,'解挂卡',23,'oprevertcard_employee'),(146,'同步人员到设备',23,'opsynctodevice_employee'),(147,'职务调动',23,'optitilechange_employee'),(148,'上传个人照片',23,'opuploadphoto_employee'),(149,'新增',23,'add_employee'),(150,'修改',23,'change_employee'),(151,'删除',23,'delete_employee'),(152,'导出',23,'dataexport_employee'),(153,'导入',23,'dataimport_employee'),(154,'浏览人员发卡',27,'browse_issuecard'),(155,'批量发卡',27,'opbatchissuecard_issuecard'),(156,'新增',27,'add_issuecard'),(157,'修改',27,'change_issuecard'),(158,'删除',27,'delete_issuecard'),(159,'导出',27,'dataexport_issuecard'),(160,'浏览人员离职',25,'browse_leavelog'),(161,'关闭门禁',25,'opcloseaccess_leavelog'),(162,'关闭考勤',25,'opcloseatt_leavelog'),(163,'离职恢复',25,'oprestoreempleave_leavelog'),(164,'新增',25,'add_leavelog'),(165,'',25,'change_leavelog'),(166,'删除',25,'delete_leavelog'),(167,'导出',25,'dataexport_leavelog'),(168,'导航',6,'can_PersonnelGuide'),(169,'Can add 人事报表',24,'add_empitemdefine'),(170,'Can change 人事报表',24,'change_empitemdefine'),(171,'Can delete 人事报表',24,'delete_empitemdefine'),(172,'数据清理',6,'can_DeleteData'),(173,'浏览系统提醒设置',30,'browse_groupmsg'),(174,'新增',30,'add_groupmsg'),(175,'修改',30,'change_groupmsg'),(176,'删除',30,'delete_groupmsg'),(177,'导出',30,'dataexport_groupmsg'),(178,'浏览公告发布',32,'browse_instantmsg'),(179,'新增',32,'add_instantmsg'),(180,'修改',32,'change_instantmsg'),(181,'删除',32,'delete_instantmsg'),(182,'导出',32,'dataexport_instantmsg'),(183,'浏览公告类别',29,'browse_msgtype'),(184,'新增',29,'add_msgtype'),(185,'修改',29,'change_msgtype'),(186,'删除',29,'delete_msgtype'),(187,'导出',29,'dataexport_msgtype'),(188,'浏览用户消息确认',31,'browse_usrmsg'),(189,'新增',31,'add_usrmsg'),(190,'修改',31,'change_usrmsg'),(191,'删除',31,'delete_usrmsg'),(192,'导出',31,'dataexport_usrmsg'),(193,'补签卡',6,'can_SelfCheckexact'),(194,'加班单',6,'can_SelfOverTime'),(195,'考勤报表',6,'can_SelfReport'),(196,'请假',6,'can_SelfSpecDay'),(197,'原始记录表',6,'can_SelfTransaction'),(198,'预约管理',6,'can_SelfVisitorReservation'),(199,'浏览区域管理',43,'browse_areaadmin'),(200,'浏览夏令时',33,'browse_dstime'),(201,'设置夏令时',33,'opsetdstime_dstime'),(202,'新增',33,'add_dstime'),(203,'修改',33,'change_dstime'),(204,'删除',33,'delete_dstime'),(205,'导出',33,'dataexport_dstime'),(206,'浏览部门管理',42,'browse_deptadmin'),(207,'浏览服务器下发命令',36,'browse_devcmd'),(208,'清空命令表',36,'opcleardevcmd_devcmd'),(209,'新增',36,'add_devcmd'),(210,'修改',36,'change_devcmd'),(211,'删除',36,'delete_devcmd'),(212,'导出',36,'dataexport_devcmd'),(213,'浏览失败命令查询',41,'browse_devcmdbak'),(214,'清空失败命令',41,'opcleardevcmd_devcmdbak'),(215,'新增',41,'add_devcmdbak'),(216,'修改',41,'change_devcmdbak'),(217,'删除',41,'delete_devcmdbak'),(218,'导出',41,'dataexport_devcmdbak'),(219,'浏览设备通讯日志',40,'browse_devlog'),(220,'导出',40,'dataexport_devlog'),(221,'设备监控',6,'can_DevRTMonitorPage'),(222,'浏览设备',34,'browse_device'),(223,'清除全部数据',34,'cleardata_device'),(224,'清除考勤图片',34,'clearpicture_device'),(225,'清除考勤记录',34,'cleartransaction_device'),(226,'设备功能',34,'devfunon_device'),(227,'修改IP地址',34,'opchangeipofacpanel_device'),(228,'修改指纹比对阈值',34,'opchangemthreshold_device'),(229,'控制辅助输出',34,'opctrlauxout_device'),(230,'禁用',34,'opdisabledevice_device'),(231,'启用',34,'openabledevice_device'),(232,'重新上传数据',34,'opreloaddata_device'),(233,'禁用夏令时',34,'opremovedstime_device'),(234,'搜索门禁控制器',34,'opsearchacpanel_device'),(235,'启用夏令时',34,'opsetdstime_device'),(236,'升级固件',34,'opupgradefirmware_device'),(237,'重启设备',34,'reboot_device'),(238,'获取设备信息',34,'refreshdeviceinfo_device'),(239,'修改通讯密码',34,'resetpassword_device'),(240,'同步时间',34,'syncacpaneltime_device'),(241,'同步所有数据',34,'syncdata_device'),(242,'获取事件记录',34,'uploadlogs_device'),(243,'获取人员信息',34,'uploaduserinfo_device'),(244,'新增',34,'add_device'),(245,'修改',34,'change_device'),(246,'删除',34,'delete_device'),(247,'导出',34,'dataexport_device'),(248,'导航',6,'can_IclockGuide'),(249,'浏览操作设备日志',39,'browse_oplog'),(250,'Transaction Monitor',39,'monitor_oplog'),(251,'浏览通信命令详情',35,'browse_operatecmd'),(252,'新增',35,'add_operatecmd'),(253,'编辑',35,'change_operatecmd'),(254,'删除',35,'delete_operatecmd'),(255,'导出',35,'dataexport_operatecmd'),(256,'浏览人员指纹',37,'browse_template'),(257,'新增',37,'add_template'),(258,'修改',37,'change_template'),(259,'删除',37,'delete_template'),(260,'导出',37,'dataexport_template'),(261,'浏览test data',44,'browse_testdata'),(262,'新增',44,'add_testdata'),(263,'修改',44,'change_testdata'),(264,'删除',44,'delete_testdata'),(265,'导出',44,'dataexport_testdata'),(266,'浏览原始记录表',38,'browse_transaction'),(267,'Clear Obsolete Data',38,'clearObsoleteData_transaction'),(268,'导出',38,'dataexport_transaction'),(269,'Can add 原始记录表',38,'add_transaction'),(270,'Can change 原始记录表',38,'change_transaction'),(271,'Can delete 原始记录表',38,'delete_transaction'),(272,'Can add 操作设备日志',39,'add_oplog'),(273,'Can change 操作设备日志',39,'change_oplog'),(274,'Can delete 操作设备日志',39,'delete_oplog'),(275,'Can add 设备通讯日志',40,'add_devlog'),(276,'Can change 设备通讯日志',40,'change_devlog'),(277,'Can delete 设备通讯日志',40,'delete_devlog'),(278,'Can add 部门管理',42,'add_deptadmin'),(279,'Can change 部门管理',42,'change_deptadmin'),(280,'Can delete 部门管理',42,'delete_deptadmin'),(281,'Can add 区域管理',43,'add_areaadmin'),(282,'Can change 区域管理',43,'change_areaadmin'),(283,'Can delete 区域管理',43,'delete_areaadmin'),(284,'考勤计算与报表',6,'can_AttCalculate'),(285,'考勤设备管理',6,'can_AttDeviceDataManage'),(286,'区域用户管理',6,'can_AttDeviceUserManage'),(287,'浏览att exception',57,'browse_attexception'),(288,'新增',57,'add_attexception'),(289,'修改',57,'change_attexception'),(290,'删除',57,'delete_attexception'),(291,'导出',57,'dataexport_attexception'),(292,'导航',6,'can_AttGuide'),(293,'浏览考勤参数',54,'browse_attparam'),(294,'新增',54,'add_attparam'),(295,'修改',54,'change_attparam'),(296,'删除',54,'delete_attparam'),(297,'导出',54,'dataexport_attparam'),(298,'浏览考勤报表',60,'browse_attreport'),(299,'统计结果详情',60,'calcresultdetail_attreport'),(300,'考勤汇总表',60,'calctotalreport_attreport'),(301,'统计',60,'calculate_attreport'),(302,'补签记录表',60,'checkexact_attreport'),(303,'每日考勤统计表',60,'earchdayattreport_attreport'),(304,'考勤异常表',60,'exceptionreport_attreport'),(305,'假类汇总',60,'leavetotalreport_attreport'),(306,'原始记录表',60,'orgbrushrecord_attreport'),(307,'其它考勤异常表',60,'otherexceptionreport_attreport'),(308,'导出',60,'dataexport_attreport'),(309,'员工排班',6,'can_AttUserOfRun'),(310,'浏览补签卡',61,'browse_checkexact'),(311,'新增补签卡',61,'opaddmanycheckexact_checkexact'),(312,'审批',61,'opauditcheckexact_checkexact'),(313,'新增',61,'add_checkexact'),(314,'修改',61,'change_checkexact'),(315,'删除',61,'delete_checkexact'),(316,'导出',61,'dataexport_checkexact'),(317,'浏览请假',52,'browse_empspecday'),(318,'新增请假',52,'opaddmanyuserid_empspecday'),(319,'审批',52,'opspecaudit_empspecday'),(320,'新增',52,'add_empspecday'),(321,'修改',52,'change_empspecday'),(322,'删除',52,'delete_empspecday'),(323,'导出',52,'dataexport_empspecday'),(324,'浏览考勤节假日',45,'browse_holiday'),(325,'新增',45,'add_holiday'),(326,'修改',45,'change_holiday'),(327,'删除',45,'delete_holiday'),(328,'导出',45,'dataexport_holiday'),(329,'浏览假类',51,'browse_leaveclass'),(330,'新增',51,'add_leaveclass'),(331,'修改',51,'change_leaveclass'),(332,'清空记录',51,'clear_leaveclass'),(333,'删除',51,'delete_leaveclass'),(334,'导出',51,'dataexport_leaveclass'),(335,'浏览统计项目表',53,'browse_leaveclass1'),(336,'新增',53,'add_leaveclass1'),(337,'修改',53,'change_leaveclass1'),(338,'删除',53,'delete_leaveclass1'),(339,'导出',53,'dataexport_leaveclass1'),(340,'浏览班次',47,'browse_num_run'),(341,'增加时间段',47,'opaddtimetable_num_run'),(342,'清空时间段',47,'opdeletetimetable_num_run'),(343,'新增',47,'add_num_run'),(344,'修改',47,'change_num_run'),(345,'删除',47,'delete_num_run'),(346,'导出',47,'dataexport_num_run'),(347,'浏览班次明细',48,'browse_num_run_deil'),(348,'新增',48,'add_num_run_deil'),(349,'修改',48,'change_num_run_deil'),(350,'删除',48,'delete_num_run_deil'),(351,'导出',48,'dataexport_num_run_deil'),(352,'浏览加班单',64,'browse_overtime'),(353,'新增加班单',64,'opaddmanyovertime_overtime'),(354,'审批',64,'opauditmanyemployee_overtime'),(355,'新增',64,'add_overtime'),(356,'修改',64,'change_overtime'),(357,'删除',64,'delete_overtime'),(358,'导出',64,'dataexport_overtime'),(359,'浏览考勤时段',46,'browse_schclass'),(360,'新增',46,'add_schclass'),(361,'修改',46,'change_schclass'),(362,'删除',46,'delete_schclass'),(363,'导出',46,'dataexport_schclass'),(364,'浏览调休',62,'browse_setuseratt'),(365,'新增',62,'opaddmanyobj_setuseratt'),(366,'新增',62,'add_setuseratt'),(367,'修改',62,'change_setuseratt'),(368,'删除',62,'delete_setuseratt'),(369,'导出',62,'dataexport_setuseratt'),(370,'浏览员工排班',50,'browse_user_of_run'),(371,'新增临时排班',50,'opaddtempshifts_user_of_run'),(372,'新增排班',50,'opadduserofrun_user_of_run'),(373,'清除排班记录',50,'opclearshift_user_of_run'),(374,'新增',50,'add_user_of_run'),(375,'修改',50,'change_user_of_run'),(376,'删除',50,'delete_user_of_run'),(377,'导出',50,'dataexport_user_of_run'),(378,'浏览临时排班',49,'browse_user_temp_sch'),(379,'清除临时排班记录',49,'opclearshift_user_temp_sch'),(380,'新增',49,'add_user_temp_sch'),(381,'修改',49,'change_user_temp_sch'),(382,'删除',49,'delete_user_temp_sch'),(383,'浏览',49,'dataexport_user_temp_sch'),(384,'浏览user used s classes',55,'browse_userusedsclasses'),(385,'浏览wait for process data',63,'browse_waitforprocessdata'),(386,'新增',63,'add_waitforprocessdata'),(387,'修改',63,'change_waitforprocessdata'),(388,'删除',63,'delete_waitforprocessdata'),(389,'导出',63,'dataexport_waitforprocessdata'),(390,'浏览att calc log',56,'browse_attcalclog'),(391,'浏览统计结果详情',58,'browse_attrecabnormite'),(392,'浏览考勤明细表',59,'browse_attshifts'),(393,'Can add user used s classes',55,'add_userusedsclasses'),(394,'Can change user used s classes',55,'change_userusedsclasses'),(395,'Can delete user used s classes',55,'delete_userusedsclasses'),(396,'Can add att calc log',56,'add_attcalclog'),(397,'Can change att calc log',56,'change_attcalclog'),(398,'Can delete att calc log',56,'delete_attcalclog'),(399,'Can add 统计结果详情',58,'add_attrecabnormite'),(400,'Can change 统计结果详情',58,'change_attrecabnormite'),(401,'Can delete 统计结果详情',58,'delete_attrecabnormite'),(402,'Can add 考勤明细表',59,'add_attshifts'),(403,'Can change 考勤明细表',59,'change_attshifts'),(404,'Can delete 考勤明细表',59,'delete_attshifts'),(405,'Can add 考勤报表',60,'add_attreport'),(406,'Can change 考勤报表',60,'change_attreport'),(407,'Can delete 考勤报表',60,'delete_attreport'),(408,'浏览反潜设置',76,'browse_accantiback'),(409,'新增',76,'add_accantiback'),(410,'修改',76,'change_accantiback'),(411,'删除',76,'delete_accantiback'),(412,'导出',76,'dataexport_accantiback'),(413,'浏览门禁设备扩展参数',70,'browse_accdevice'),(414,'新增',70,'add_accdevice'),(415,'修改',70,'change_accdevice'),(416,'删除',70,'delete_accdevice'),(417,'导出',70,'dataexport_accdevice'),(418,'浏览门',68,'browse_accdoor'),(419,'新增',68,'add_accdoor'),(420,'修改',68,'change_accdoor'),(421,'删除',68,'delete_accdoor'),(422,'导出',68,'dataexport_accdoor'),(423,'浏览首卡常开设置',73,'browse_accfirstopen'),(424,'添加开门人员',73,'opaddemptofcopen_accfirstopen'),(425,'删除开门人员',73,'opdelempfromfcopen_accfirstopen'),(426,'新增',73,'add_accfirstopen'),(427,'修改',73,'change_accfirstopen'),(428,'删除',73,'delete_accfirstopen'),(429,'导出',73,'dataexport_accfirstopen'),(430,'浏览全局反潜设置',81,'browse_accglobalapb'),(431,'新增',81,'add_accglobalapb'),(432,'修改',81,'change_accglobalapb'),(433,'删除',81,'delete_accglobalapb'),(434,'导出',81,'dataexport_accglobalapb'),(435,'浏览全局反潜组设置',80,'browse_accglobalapbgroup'),(436,'新增',80,'add_accglobalapbgroup'),(437,'修改',80,'change_accglobalapbgroup'),(438,'删除',80,'delete_accglobalapbgroup'),(439,'导出',80,'dataexport_accglobalapbgroup'),(440,'浏览门禁节假日',78,'browse_accholidays'),(441,'新增',78,'add_accholidays'),(442,'修改',78,'change_accholidays'),(443,'删除',78,'delete_accholidays'),(444,'导出',78,'dataexport_accholidays'),(445,'浏览互锁设置',77,'browse_accinterlock'),(446,'新增',77,'add_accinterlock'),(447,'修改',77,'change_accinterlock'),(448,'删除',77,'delete_accinterlock'),(449,'导出',77,'dataexport_accinterlock'),(450,'浏览门禁权限组',79,'browse_acclevelset'),(451,'添加人员',79,'opaddemptolevel_acclevelset'),(452,'删除人员',79,'opdelempfromlevel_acclevelset'),(453,'新增',79,'add_acclevelset'),(454,'修改',79,'change_acclevelset'),(455,'删除',79,'delete_acclevelset'),(456,'导出',79,'dataexport_acclevelset'),(457,'浏览联动设置',72,'browse_acclinkageio'),(458,'新增',72,'add_acclinkageio'),(459,'修改',72,'change_acclinkageio'),(460,'删除',72,'delete_acclinkageio'),(461,'导出',72,'dataexport_acclinkageio'),(462,'浏览电子地图',66,'browse_accmap'),(463,'添加门',66,'opadddoorsontomap_accmap'),(464,'放大',66,'openlargemapdoor_accmap'),(465,'缩小',66,'opreducemapdoor_accmap'),(466,'移除门',66,'opremovedoorfrommap_accmap'),(467,'保存位置信息',66,'opsavemapdoorpos_accmap'),(468,'新增',66,'add_accmap'),(469,'修改',66,'change_accmap'),(470,'删除',66,'delete_accmap'),(471,'导出',66,'dataexport_accmap'),(472,'浏览门坐标',69,'browse_accmapdoorpos'),(473,'新增',69,'add_accmapdoorpos'),(474,'修改',69,'change_accmapdoorpos'),(475,'删除',69,'delete_accmapdoorpos'),(476,'导出',69,'dataexport_accmapdoorpos'),(477,'浏览多卡开门组',75,'browse_accmorecardgroup'),(478,'新增',75,'add_accmorecardgroup'),(479,'修改',75,'change_accmorecardgroup'),(480,'删除',75,'delete_accmorecardgroup'),(481,'导出',75,'dataexport_accmorecardgroup'),(482,'浏览多卡开门设置',74,'browse_accmorecardset'),(483,'新增',74,'add_accmorecardset'),(484,'修改',74,'change_accmorecardset'),(485,'删除',74,'delete_accmorecardset'),(486,'导出',74,'dataexport_accmorecardset'),(487,'门禁参数设置',6,'can_AccOption'),(488,'浏览实时监控记录',71,'browse_accrtmonitor'),(489,'清空异常事件记录',71,'opclearabnormitylogs_accrtmonitor'),(490,'清空全部事件记录',71,'opclearrtlogs_accrtmonitor'),(491,'新增',71,'add_accrtmonitor'),(492,'修改',71,'change_accrtmonitor'),(493,'删除',71,'delete_accrtmonitor'),(494,'导出',71,'dataexport_accrtmonitor'),(495,'浏览读头',82,'browse_accreader'),(496,'新增',82,'add_accreader'),(497,'修改',82,'change_accreader'),(498,'删除',82,'delete_accreader'),(499,'导出',82,'dataexport_accreader'),(500,'浏览门禁时间段',65,'browse_acctimeseg'),(501,'新增',65,'add_acctimeseg'),(502,'修改',65,'change_acctimeseg'),(503,'删除',65,'delete_acctimeseg'),(504,'导出',65,'dataexport_acctimeseg'),(505,'浏览韦根卡格式',67,'browse_accwiegandfmt'),(506,'重置默认设置',67,'initwgfmt_accwiegandfmt'),(507,'新增',67,'add_accwiegandfmt'),(508,'修改',67,'change_accwiegandfmt'),(509,'删除',67,'delete_accwiegandfmt'),(510,'导出',67,'dataexport_accwiegandfmt'),(511,'门禁异常事件',6,'can_AlarmEventReportPage'),(512,'全部门禁事件',6,'can_AllEventReportPage'),(513,'浏览辅助输入输出',83,'browse_auxiliary'),(514,'新增',83,'add_auxiliary'),(515,'修改',83,'change_auxiliary'),(516,'删除',83,'delete_auxiliary'),(517,'导出',83,'dataexport_auxiliary'),(518,'辅助点管理',6,'can_AuxiliaryPage'),(519,'门管理',6,'can_DoorMngPage'),(520,'门设置',6,'can_DoorSetPage'),(521,'电子地图',6,'can_ElectroMapPage'),(522,'浏览邮件',84,'browse_emailrecord'),(523,'清空全部邮件记录',84,'opclearrtlogs_emailrecord'),(524,'新增',84,'add_emailrecord'),(525,'修改',84,'change_emailrecord'),(526,'删除',84,'delete_emailrecord'),(527,'导出',84,'dataexport_emailrecord'),(528,'邮件',6,'can_EmailRecordFormPage'),(529,'以人员显示',6,'can_EmpLevelByEmpPage'),(530,'以权限组显示',6,'can_EmpLevelByLevelPage'),(531,'人员门禁权限',6,'can_EmpLevelReportPage'),(532,'人员门禁权限设置',6,'can_EmpLevelSetPage'),(533,'报警事件',6,'can_MonitorAlarmPage'),(534,'监控全部',6,'can_MonitorAllPage'),(535,'实时监控',6,'can_RTMonitorPage'),(536,'报表',6,'can_ReportFormPage'),(537,'人员电梯权限设置',6,'can_EleEmpLevelSetPage'),(538,'首卡常开',6,'can_EleFirstOpenPage'),(539,'以人员显示',6,'can_EmpLevelByEleEmpPage'),(540,'以权限组显示',6,'can_EmpLevelByEleLevelPage'),(541,'梯控权限组',6,'can_FloorLevelSetPage'),(542,'楼层设置',6,'can_FloorMngPage'),(543,'通道管理',6,'can_ChannelMngPage'),(544,'监控时是否弹出',6,'can_ShowVideoWhileMonitoring'),(545,'浏览视频通道',85,'browse_vidchannel'),(546,'新增',85,'add_vidchannel'),(547,'修改',85,'change_vidchannel'),(548,'删除',85,'delete_vidchannel'),(549,'导出',85,'dataexport_vidchannel'),(550,'视频参数设置',6,'can_VidOption'),(551,'视频事件记录',6,'can_VideoEventPage'),(552,'视频联动记录',6,'can_VideoLinkagePage'),(553,'浏览视频通道坐标',86,'browse_videomapchannelpos'),(554,'新增',86,'add_videomapchannelpos'),(555,'修改',86,'change_videomapchannelpos'),(556,'删除',86,'delete_videomapchannelpos'),(557,'导出',86,'dataexport_videomapchannelpos'),(558,'视频预览',6,'can_VideoPreviewPage'),(559,'访客基本资料',6,'can_BaseDataPage'),(560,'浏览登记地点',89,'browse_visplace'),(561,'新增',89,'add_visplace'),(562,'修改',89,'change_visplace'),(563,'删除',89,'delete_visplace'),(564,'导出',89,'dataexport_visplace'),(565,'浏览来访事由 ',87,'browse_visreason'),(566,'新增',87,'add_visreason'),(567,'修改',87,'change_visreason'),(568,'删除',87,'delete_visreason'),(569,'导出',87,'dataexport_visreason'),(570,'浏览访客历史记录',91,'browse_visreport'),(571,'新增',91,'add_visreport'),(572,'详情',91,'change_visreport'),(573,'删除',91,'delete_visreport'),(574,'导出',91,'dataexport_visreport'),(575,'浏览预约管理',88,'browse_visreservation'),(576,'新增',88,'add_visreservation'),(577,'修改',88,'change_visreservation'),(578,'删除',88,'delete_visreservation'),(579,'导出',88,'dataexport_visreservation'),(580,'浏览访客管理',90,'browse_visvisitor'),(581,'离开登记',90,'opleaveregister_visvisitor'),(582,'进入登记',90,'add_visvisitor'),(583,'编辑',90,'change_visvisitor'),(584,'删除',90,'delete_visvisitor'),(585,'导出',90,'dataexport_visvisitor'),(586,'访客单',6,'can_VisitorFormPage'),(587,'访客权限设置',6,'can_VisitorLevelSetPage'),(588,'参数设置',6,'can_VisitorOptionPage');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL auto_increment,
  `username` varchar(30) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `email` varchar(75) NOT NULL,
  `password` varchar(128) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `last_login` datetime NOT NULL,
  `date_joined` datetime NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'admin','','','','sha1$44a07$fca75fd498dd928870f72fe4e082e096a030f505',1,1,1,'2025-10-20 09:29:39','2025-10-06 15:12:42'),(2,'employee','','','employee@sinna.com','sha1$c3630$2713835efb9af4864679b58c1e2a1f424967fc7f',1,1,0,'2025-10-06 15:12:42','2025-10-06 15:12:42');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
CREATE TABLE `auth_user_groups` (
  `id` int(11) NOT NULL auto_increment,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `user_id` (`user_id`,`group_id`),
  KEY `auth_user_groups_user_id` (`user_id`),
  KEY `auth_user_groups_group_id` (`group_id`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
INSERT INTO `auth_user_groups` VALUES (1,2,1);
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
CREATE TABLE `auth_user_user_permissions` (
  `id` int(11) NOT NULL auto_increment,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `user_id` (`user_id`,`permission_id`),
  KEY `auth_user_user_permissions_user_id` (`user_id`),
  KEY `auth_user_user_permissions_permission_id` (`permission_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `base_additiondata`
--

DROP TABLE IF EXISTS `base_additiondata`;
CREATE TABLE `base_additiondata` (
  `id` int(11) NOT NULL auto_increment,
  `create_time` datetime NOT NULL,
  `user_id` int(11) default NULL,
  `content_type_id` int(11) default NULL,
  `object_id` varchar(100) NOT NULL,
  `key` varchar(64) NOT NULL,
  `value` varchar(128) NOT NULL,
  `data` longtext NOT NULL,
  `delete_time` datetime default NULL,
  PRIMARY KEY  (`id`),
  KEY `base_additiondata_user_id` (`user_id`),
  KEY `base_additiondata_content_type_id` (`content_type_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `base_additiondata`
--

LOCK TABLES `base_additiondata` WRITE;
/*!40000 ALTER TABLE `base_additiondata` DISABLE KEYS */;
/*!40000 ALTER TABLE `base_additiondata` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `base_appoption`
--

DROP TABLE IF EXISTS `base_appoption`;
CREATE TABLE `base_appoption` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `optname` varchar(50) NOT NULL,
  `value` varchar(100) NOT NULL,
  `discribe` varchar(100) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `base_appoption`
--

LOCK TABLES `base_appoption` WRITE;
/*!40000 ALTER TABLE `base_appoption` DISABLE KEYS */;
INSERT INTO `base_appoption` VALUES (1,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'company','Company Name','Company Name'),(2,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'dbversion','5.31','version'),(3,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'date_format','%m/%d/%Y','Date Format'),(4,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'browse_title','Access Control System','Browser Title');
/*!40000 ALTER TABLE `base_appoption` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `base_basecode`
--

DROP TABLE IF EXISTS `base_basecode`;
CREATE TABLE `base_basecode` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `content` varchar(30) NOT NULL,
  `content_class` int(11) default NULL,
  `display` varchar(30) default NULL,
  `value` varchar(30) NOT NULL,
  `remark` varchar(200) default NULL,
  `is_add` varchar(4) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=3847 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `base_basecode`
--

LOCK TABLES `base_basecode` WRITE;
/*!40000 ALTER TABLE `base_basecode` DISABLE KEYS */;
INSERT INTO `base_basecode` VALUES (3835,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'Simplified Chinese','zh-cn',NULL,NULL),(3836,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'English','en',NULL,NULL),(3837,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'Spanish','es',NULL,NULL),(3838,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'Traditional Chinese','zh-tw',NULL,NULL),(3839,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'Polish','pl',NULL,NULL),(3840,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'French','fr',NULL,NULL),(3841,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'Arabic','ar',NULL,NULL),(3842,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'Vietnamese','vi',NULL,NULL),(3843,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'Thai','th',NULL,NULL),(3844,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'Russian','ru',NULL,NULL),(3845,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'Portuguese','pt',NULL,NULL),(3846,NULL,'2025-10-16 07:57:16',NULL,NULL,NULL,NULL,0,'base.language',0,'Italian','it',NULL,NULL);
/*!40000 ALTER TABLE `base_basecode` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `base_datatranslation`
--

DROP TABLE IF EXISTS `base_datatranslation`;
CREATE TABLE `base_datatranslation` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `content_type_id` int(11) default NULL,
  `property` varchar(100) NOT NULL,
  `language` varchar(10) NOT NULL,
  `value` varchar(200) NOT NULL,
  `display` varchar(400) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `base_datatranslation_content_type_id` (`content_type_id`)
) ENGINE=MyISAM AUTO_INCREMENT=17 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `base_datatranslation`
--

LOCK TABLES `base_datatranslation` WRITE;
/*!40000 ALTER TABLE `base_datatranslation` DISABLE KEYS */;
INSERT INTO `base_datatranslation` VALUES (1,NULL,'2025-10-06 15:14:14','admin','2025-10-06 15:14:14',NULL,NULL,0,6,'app_label','en','worktable','worktable'),(2,NULL,'2025-10-06 15:14:14','admin','2025-10-06 15:14:14',NULL,NULL,0,6,'app_label','en','dbapp','dbapp'),(3,NULL,'2025-10-06 15:14:14','admin','2025-10-06 15:14:14',NULL,NULL,0,6,'app_label','en','auth','auth'),(4,NULL,'2025-10-06 15:14:14','admin','2025-10-06 15:14:14',NULL,NULL,0,6,'app_label','en','django_extensions','django_extensions'),(5,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','Simplified Chinese','Simplified Chinese'),(6,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','English','English'),(7,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','Spanish','Spanish'),(8,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','Traditional Chinese','Traditional Chinese'),(9,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','Polish','Polish'),(10,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','French','French'),(11,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','Arabic','Arabic'),(12,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','Vietnamese','Vietnamese'),(13,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','Thai','Thai'),(14,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','Russian','Russian'),(15,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','Portuguese','Portuguese'),(16,NULL,'2025-10-06 15:15:08','admin','2025-10-06 15:15:08',NULL,NULL,0,12,'display','en','Italian','Italian');
/*!40000 ALTER TABLE `base_datatranslation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `base_operatortemplate`
--

DROP TABLE IF EXISTS `base_operatortemplate`;
CREATE TABLE `base_operatortemplate` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `user_id` int(11) NOT NULL,
  `template1` longtext,
  `finger_id` smallint(6) NOT NULL,
  `valid` smallint(6) NOT NULL,
  `fpversion` varchar(10) NOT NULL,
  `bio_type` smallint(6) NOT NULL,
  `utime` datetime default NULL,
  `bitmap_picture` longtext,
  `bitmap_picture2` longtext,
  `bitmap_picture3` longtext,
  `bitmap_picture4` longtext,
  `use_type` smallint(6) default NULL,
  `template2` longtext,
  `template3` longtext,
  `template_flag` tinyint(1) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `user_id` (`user_id`,`finger_id`,`fpversion`),
  KEY `base_operatortemplate_user_id` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `base_operatortemplate`
--

LOCK TABLES `base_operatortemplate` WRITE;
/*!40000 ALTER TABLE `base_operatortemplate` DISABLE KEYS */;
/*!40000 ALTER TABLE `base_operatortemplate` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `base_option`
--

DROP TABLE IF EXISTS `base_option`;
CREATE TABLE `base_option` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `name` varchar(30) NOT NULL,
  `app_label` varchar(30) NOT NULL,
  `catalog` varchar(30) NOT NULL,
  `group` varchar(30) NOT NULL,
  `widget` varchar(400) NOT NULL,
  `required` tinyint(1) NOT NULL,
  `validator` varchar(400) NOT NULL,
  `verbose_name` varchar(80) NOT NULL,
  `help_text` varchar(160) NOT NULL,
  `visible` tinyint(1) NOT NULL,
  `default` varchar(100) NOT NULL,
  `read_only` tinyint(1) NOT NULL,
  `for_personal` tinyint(1) NOT NULL,
  `type` varchar(50) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=20 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `base_option`
--

LOCK TABLES `base_option` WRITE;
/*!40000 ALTER TABLE `base_option` DISABLE KEYS */;
INSERT INTO `base_option` VALUES (1,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'date_format','base','2','','',0,'','Date Format','',1,'%Y-%m-%d',0,1,'CharField'),(2,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'time_format','base','2','','',0,'','Time Format','',1,'%H:%M:%S',0,1,'CharField'),(3,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'datetime_format','base','2','','',0,'','Datetime Format','',1,'%Y-%m-%d %H:%M:%S',0,1,'CharField'),(4,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'shortdate_format','base','2','','',0,'','Shortdate format','',1,'%y-%m-%d',0,1,'CharField'),(5,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'shortdatetime_format','base','2','','',0,'','Shortdatetime Format','',1,'%y-%m-%d %H:%M',0,1,'CharField'),(6,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'language','base','2','','',0,'','语言','',1,'en',0,1,'CharField'),(7,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'base_default_page','base','2','','',0,'','System Default Page','',0,'data/auth/User/',0,1,'CharField'),(8,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'site_default_page','base','2','','',0,'','System Default Page','',0,'data/worktable/',0,1,'CharField'),(9,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'site_device_page','base','2','','',0,'','Device List Page','',0,'data/iclock/device/',0,1,'CharField'),(10,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'backup_sched','base','1','','',0,'','备份时间','',1,'',0,1,'CharField'),(11,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'max_photo_width','dbapp','2','','',0,'','Maximum Image Width','',1,'800',0,1,'CharField'),(12,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'theme','dbapp','2','','',0,'','Style','',1,'flat',0,1,'CharField'),(13,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'personnel_default_page','personnel','2','','',0,'','Default access control page','',0,'data/personnel/Employee/',0,1,'CharField'),(14,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'iclock_default_page','iclock','2','','',0,'','Default access control page','',0,'data/iclock/device/',0,1,'CharField'),(15,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,'att_default_page','att','2','','',0,'','default access control page','',0,'data/att/EmpSpecDay/',0,1,'CharField'),(16,NULL,'2025-10-06 15:12:45',NULL,'2025-10-06 15:12:45',NULL,NULL,0,'iaccess_default_page','iaccess','2','','',0,'','default access control page','',0,'iaccess/RTMonitorPage/',0,1,'CharField'),(17,NULL,'2025-10-06 15:12:45',NULL,'2025-10-06 15:12:45',NULL,NULL,0,'elevator_default_page','elevator','2','','',0,'','Default Page of Elevator Control System','',0,'elevator/FloorMngPage/',0,1,'CharField'),(18,NULL,'2025-10-06 15:12:45',NULL,'2025-10-06 15:12:45',NULL,NULL,0,'video_default_page','video','2','','',0,'','Default page of Video','',0,'video/VideoPreviewPage/',0,1,'CharField'),(19,NULL,'2025-10-06 15:12:45',NULL,'2025-10-06 15:12:45',NULL,NULL,0,'visitor_default_page','visitor','2','','',0,'','Visitors default Page','',0,'data/visitor/VisVisitor/',0,1,'CharField');
/*!40000 ALTER TABLE `base_option` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `base_personaloption`
--

DROP TABLE IF EXISTS `base_personaloption`;
CREATE TABLE `base_personaloption` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `option_id` int(11) NOT NULL,
  `value` varchar(100) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `option_id` (`option_id`,`user_id`),
  KEY `base_personaloption_option_id` (`option_id`),
  KEY `base_personaloption_user_id` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `base_personaloption`
--

LOCK TABLES `base_personaloption` WRITE;
/*!40000 ALTER TABLE `base_personaloption` DISABLE KEYS */;
/*!40000 ALTER TABLE `base_personaloption` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `base_strresource`
--

DROP TABLE IF EXISTS `base_strresource`;
CREATE TABLE `base_strresource` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `app` varchar(20) default NULL,
  `str` varchar(400) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `base_strresource`
--

LOCK TABLES `base_strresource` WRITE;
/*!40000 ALTER TABLE `base_strresource` DISABLE KEYS */;
/*!40000 ALTER TABLE `base_strresource` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `base_strtranslation`
--

DROP TABLE IF EXISTS `base_strtranslation`;
CREATE TABLE `base_strtranslation` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `str_id` int(11) NOT NULL,
  `language` varchar(10) NOT NULL,
  `display` varchar(400) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `base_strtranslation_str_id` (`str_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `base_strtranslation`
--

LOCK TABLES `base_strtranslation` WRITE;
/*!40000 ALTER TABLE `base_strtranslation` DISABLE KEYS */;
/*!40000 ALTER TABLE `base_strtranslation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `base_systemoption`
--

DROP TABLE IF EXISTS `base_systemoption`;
CREATE TABLE `base_systemoption` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `option_id` int(11) NOT NULL,
  `value` varchar(100) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `base_systemoption_option_id` (`option_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `base_systemoption`
--

LOCK TABLES `base_systemoption` WRITE;
/*!40000 ALTER TABLE `base_systemoption` DISABLE KEYS */;
/*!40000 ALTER TABLE `base_systemoption` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `checkexact`
--

DROP TABLE IF EXISTS `checkexact`;
CREATE TABLE `checkexact` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `UserID` int(11) NOT NULL,
  `CHECKTIME` datetime NOT NULL,
  `CHECKTYPE` varchar(5) NOT NULL,
  `ISADD` smallint(6) default NULL,
  `YUYIN` varchar(100) default NULL,
  `ISMODIFY` smallint(6) default NULL,
  `ISDELETE` smallint(6) default NULL,
  `INCOUNT` smallint(6) default NULL,
  `ISCOUNT` smallint(6) default NULL,
  `MODIFYBY` varchar(20) default NULL,
  `DATE` datetime default NULL,
  `audit_status` smallint(6) default NULL,
  `audit_reason` varchar(100) default NULL,
  PRIMARY KEY  (`id`),
  KEY `checkexact_UserID` (`UserID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `checkexact`
--

LOCK TABLES `checkexact` WRITE;
/*!40000 ALTER TABLE `checkexact` DISABLE KEYS */;
/*!40000 ALTER TABLE `checkexact` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `checkinout`
--

DROP TABLE IF EXISTS `checkinout`;
CREATE TABLE `checkinout` (
  `id` int(11) NOT NULL auto_increment,
  `userid` int(11) NOT NULL,
  `checktime` datetime NOT NULL,
  `checktype` varchar(5) NOT NULL,
  `verifycode` int(11) NOT NULL,
  `SN` int(11) default NULL,
  `sensorid` varchar(5) default NULL,
  `WorkCode` varchar(20) default NULL,
  `Reserved` varchar(20) default NULL,
  `sn_name` varchar(40) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `userid` (`userid`,`checktime`),
  KEY `checkinout_userid` (`userid`),
  KEY `checkinout_SN` (`SN`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `checkinout`
--

LOCK TABLES `checkinout` WRITE;
/*!40000 ALTER TABLE `checkinout` DISABLE KEYS */;
/*!40000 ALTER TABLE `checkinout` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dbapp_viewmodel`
--

DROP TABLE IF EXISTS `dbapp_viewmodel`;
CREATE TABLE `dbapp_viewmodel` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `model_id` int(11) NOT NULL,
  `name` varchar(200) NOT NULL,
  `info` longtext NOT NULL,
  `viewtype` varchar(20) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `dbapp_viewmodel_model_id` (`model_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `dbapp_viewmodel`
--

LOCK TABLES `dbapp_viewmodel` WRITE;
/*!40000 ALTER TABLE `dbapp_viewmodel` DISABLE KEYS */;
/*!40000 ALTER TABLE `dbapp_viewmodel` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dbbackuplog`
--

DROP TABLE IF EXISTS `dbbackuplog`;
CREATE TABLE `dbbackuplog` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `user_id` int(11) NOT NULL,
  `starttime` datetime default NULL,
  `imflag` tinyint(1) NOT NULL,
  `successflag` varchar(1) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `dbbackuplog_user_id` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `dbbackuplog`
--

LOCK TABLES `dbbackuplog` WRITE;
/*!40000 ALTER TABLE `dbbackuplog` DISABLE KEYS */;
/*!40000 ALTER TABLE `dbbackuplog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `departments`
--

DROP TABLE IF EXISTS `departments`;
CREATE TABLE `departments` (
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `DeptID` int(11) NOT NULL auto_increment,
  `DeptName` varchar(100) NOT NULL,
  `code` varchar(100) NOT NULL,
  `supdeptid` int(11) default NULL,
  `type` varchar(10) NOT NULL,
  `invalidate` date default NULL,
  PRIMARY KEY  (`DeptID`),
  KEY `departments_supdeptid` (`supdeptid`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `departments`
--

LOCK TABLES `departments` WRITE;
/*!40000 ALTER TABLE `departments` DISABLE KEYS */;
INSERT INTO `departments` VALUES (NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,1,'Department Name','1',NULL,'dept',NULL);
/*!40000 ALTER TABLE `departments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `deptadmin`
--

DROP TABLE IF EXISTS `deptadmin`;
CREATE TABLE `deptadmin` (
  `id` int(11) NOT NULL auto_increment,
  `user_id` int(11) NOT NULL,
  `dept_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `deptadmin_user_id` (`user_id`),
  KEY `deptadmin_dept_id` (`dept_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `deptadmin`
--

LOCK TABLES `deptadmin` WRITE;
/*!40000 ALTER TABLE `deptadmin` DISABLE KEYS */;
/*!40000 ALTER TABLE `deptadmin` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `devcmds`
--

DROP TABLE IF EXISTS `devcmds`;
CREATE TABLE `devcmds` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `SN_id` int(11) default NULL,
  `CmdOperate_id` int(11) default NULL,
  `CmdContent` longtext NOT NULL,
  `CmdCommitTime` datetime NOT NULL,
  `CmdTransTime` datetime default NULL,
  `CmdOverTime` datetime default NULL,
  `CmdReturn` int(11) default NULL,
  `CmdReturnContent` longtext,
  `CmdImmediately` tinyint(1) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `devcmds_SN_id` (`SN_id`),
  KEY `devcmds_CmdOperate_id` (`CmdOperate_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `devcmds`
--

LOCK TABLES `devcmds` WRITE;
/*!40000 ALTER TABLE `devcmds` DISABLE KEYS */;
/*!40000 ALTER TABLE `devcmds` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `devcmds_bak`
--

DROP TABLE IF EXISTS `devcmds_bak`;
CREATE TABLE `devcmds_bak` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `SN_id` int(11) default NULL,
  `CmdOperate_id` int(11) default NULL,
  `CmdContent` longtext NOT NULL,
  `CmdCommitTime` datetime NOT NULL,
  `CmdTransTime` datetime default NULL,
  `CmdOverTime` datetime default NULL,
  `CmdReturn` int(11) default NULL,
  `CmdReturnContent` longtext,
  `CmdImmediately` tinyint(1) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `devcmds_bak_SN_id` (`SN_id`),
  KEY `devcmds_bak_CmdOperate_id` (`CmdOperate_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `devcmds_bak`
--

LOCK TABLES `devcmds_bak` WRITE;
/*!40000 ALTER TABLE `devcmds_bak` DISABLE KEYS */;
/*!40000 ALTER TABLE `devcmds_bak` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `devlog`
--

DROP TABLE IF EXISTS `devlog`;
CREATE TABLE `devlog` (
  `id` int(11) NOT NULL auto_increment,
  `SN_id` int(11) NOT NULL,
  `OP` varchar(40) NOT NULL,
  `Object` varchar(80) default NULL,
  `Cnt` int(11) NOT NULL,
  `ECnt` int(11) NOT NULL,
  `OpTime` datetime NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `devlog_SN_id` (`SN_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `devlog`
--

LOCK TABLES `devlog` WRITE;
/*!40000 ALTER TABLE `devlog` DISABLE KEYS */;
/*!40000 ALTER TABLE `devlog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL auto_increment,
  `name` varchar(100) NOT NULL,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `app_label` (`app_label`,`model`)
) ENGINE=MyISAM AUTO_INCREMENT=92 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'session','sessions','session'),(2,'permission','auth','permission'),(3,'Role','auth','group'),(4,'User','auth','user'),(5,'message','auth','message'),(6,'content type','contenttypes','contenttype'),(7,'Log Events','base','logentry'),(8,'Added data','base','additiondata'),(9,'Translated to data','base','datatranslation'),(10,'Translated to character string resource','base','strtranslation'),(11,'str resource','base','strresource'),(12,'Basic code table','base','basecode'),(13,'Settings','base','option'),(14,'System Parameter','base','systemoption'),(15,'System Parameter','base','appoption'),(16,'Personal option','base','personaloption'),(17,'user fingerprint','base','operatortemplate'),(18,'Database Management','dbapp','dbbackuplog'),(19,'view model','dbapp','viewmodel'),(20,'Department','personnel','department'),(21,'Multi-Card Opening Personnel Groups','personnel','accmorecardempgroup'),(22,'Area Setting','personnel','area'),(23,'Personnel','personnel','employee'),(24,'Reports','personnel','empitemdefine'),(25,'Departure','personnel','leavelog'),(26,'Card type','personnel','cardtype'),(27,'Issue Card','personnel','issuecard'),(28,'Transfer','personnel','empchange'),(29,'Notice type','worktable','msgtype'),(30,'System reminder setting','worktable','groupmsg'),(31,'Confirm user information','worktable','usrmsg'),(32,'Release notice','worktable','instantmsg'),(33,'Daylight Saving Time','iclock','dstime'),(34,'Device','iclock','device'),(35,'Command details','iclock','operatecmd'),(36,'Server Sent Commands','iclock','devcmd'),(37,'Fingerprint','iclock','template'),(38,'AC log','iclock','transaction'),(39,'Device operation log','iclock','oplog'),(40,'Device communication log','iclock','devlog'),(41,'Failed Commands For Searching','iclock','devcmdbak'),(42,'Department Management','iclock','deptadmin'),(43,'Area Management','iclock','areaadmin'),(44,'test data','iclock','testdata'),(45,'Holiday','att','holiday'),(46,'TimeTable','att','schclass'),(47,'Shift','att','num_run'),(48,'Details','att','num_run_deil'),(49,'Temporary schedule','att','user_temp_sch'),(50,'Schedule','att','user_of_run'),(51,'Type','att','leaveclass'),(52,'Exception','att','empspecday'),(53,'Statistic table','att','leaveclass1'),(54,'Parameter','att','attparam'),(55,'user used s classes','att','userusedsclasses'),(56,'att calc log','att','attcalclog'),(57,'att exception','att','attexception'),(58,'Log result','att','attrecabnormite'),(59,'Daily detail','att','attshifts'),(60,'Report','att','attreport'),(61,'Append log','att','checkexact'),(62,'Reschedule','att','setuseratt'),(63,'wait for process data','att','waitforprocessdata'),(64,'加班单','att','overtime'),(65,'Time Zones','iaccess','acctimeseg'),(66,'Map','iaccess','accmap'),(67,'Wiegand Card Format','iaccess','accwiegandfmt'),(68,'Door','iaccess','accdoor'),(69,'Door Coordinates','iaccess','accmapdoorpos'),(70,'Access control device extension parameter','iaccess','accdevice'),(71,'Real Time Monitoring Events','iaccess','accrtmonitor'),(72,'Linkage Settings','iaccess','acclinkageio'),(73,'First-Card Normal Open Settings','iaccess','accfirstopen'),(74,'Multi-Card Opening Settings','iaccess','accmorecardset'),(75,'Multi-Card Opening Group','iaccess','accmorecardgroup'),(76,'Anti-Passback Settings','iaccess','accantiback'),(77,'Interlock Settings','iaccess','accinterlock'),(78,'Holidays','iaccess','accholidays'),(79,'Access Levels','iaccess','acclevelset'),(80,'全局反潜组设置','iaccess','accglobalapbgroup'),(81,'全局反潜设置','iaccess','accglobalapb'),(82,'Reader','iaccess','accreader'),(83,'Auxiliary Point','iaccess','auxiliary'),(84,'邮件','iaccess','emailrecord'),(85,'Video Channel','video','vidchannel'),(86,'VideoMapChannelPos','video','videomapchannelpos'),(87,'Add Reason','visitor','visreason'),(88,'Reservation Manage','visitor','visreservation'),(89,'Add Entry/Exit','visitor','visplace'),(90,'Visitor Manage','visitor','visvisitor'),(91,'Visitor History','visitor','visreport');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime NOT NULL,
  PRIMARY KEY  (`session_key`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('32d24aaa39e60002c378f4e56dfe0bfd','Z0FKOWNRRlZDblJsYzNSamIyOXJhV1Z4QWxVR2QyOXlhMlZrY1FOekxnPT0KY2NhM2E4YmYwMWFk\nODcwMGFkNGI0ZDdiNzk0ZWM4ZjU=\n','2025-10-06 16:16:38'),('9e3f86c095c86e98a6130c7a5a322a03','Z0FKOWNRRW9WUkpmWVhWMGFGOTFjMlZ5WDJKaFkydGxibVJ4QWxVcFpHcGhibWR2TG1OdmJuUnlh\nV0l1WVhWMGFDNWlZV05yWlc1awpjeTVOYjJSbGJFSmhZMnRsYm1SeEExVU5YMkYxZEdoZmRYTmxj\nbDlwWkhFRWlnRUJWUTlrYW1GdVoyOWZiR0Z1WjNWaFoyVnhCVmdDCkFBQUFaVzV4Qm5VdQoyZTg3\nMWI4ZTcxMDlmYjgxZGNmZDgwMDNhMTMzMTQ5Mw==\n','2025-10-14 14:03:25'),('c573af0c21f4647b2f6140ea037498a4','Z0FKOWNRRW9WUTFmWVhWMGFGOTFjMlZ5WDJsa2NRS0tBUUZWRWw5aGRYUm9YM1Z6WlhKZlltRmph\nMlZ1WkhFRFZTbGthbUZ1WjI4dQpZMjl1ZEhKcFlpNWhkWFJvTG1KaFkydGxibVJ6TGsxdlpHVnNR\nbUZqYTJWdVpIRUVWUTlrYW1GdVoyOWZiR0Z1WjNWaFoyVnhCVmdDCkFBQUFaVzV4Qm5VdQoxYzQ3\nMGQyYWUyZTliZTkzOWMxNjhkOTJhMDkxNDk0Nw==\n','2025-10-06 16:15:30'),('0be8b36658ece604ee2a02fe12700237','Z0FKOWNRRlZDblJsYzNSamIyOXJhV1Z4QWxVR2QyOXlhMlZrY1FOekxnPT0KY2NhM2E4YmYwMWFk\nODcwMGFkNGI0ZDdiNzk0ZWM4ZjU=\n','2025-10-07 09:23:53'),('6a4324a718c4ffa35bf3020e18dc5ad3','Z0FKOWNRRlZDblJsYzNSamIyOXJhV1Z4QWxVR2QyOXlhMlZrY1FOekxnPT0KY2NhM2E4YmYwMWFk\nODcwMGFkNGI0ZDdiNzk0ZWM4ZjU=\n','2025-10-09 09:04:33'),('fbebb961090017f70c240737e04e0295','Z0FKOWNRRlZDblJsYzNSamIyOXJhV1Z4QWxVR2QyOXlhMlZrY1FOekxnPT0KY2NhM2E4YmYwMWFk\nODcwMGFkNGI0ZDdiNzk0ZWM4ZjU=\n','2025-10-16 12:24:18'),('494cb880d0674cdea5de60cbda61510b','Z0FKOWNRRW9WUkpmWVhWMGFGOTFjMlZ5WDJKaFkydGxibVJ4QWxVcFpHcGhibWR2TG1OdmJuUnlh\nV0l1WVhWMGFDNWlZV05yWlc1awpjeTVOYjJSbGJFSmhZMnRsYm1SeEExVU5YMkYxZEdoZmRYTmxj\nbDlwWkhFRWlnRUJWUTlrYW1GdVoyOWZiR0Z1WjNWaFoyVnhCVmdDCkFBQUFaVzV4Qm5VdQoyZTg3\nMWI4ZTcxMDlmYjgxZGNmZDgwMDNhMTMzMTQ5Mw==\n','2025-10-10 09:01:43'),('bc60db741e8186675831bd22d649e9dc','Z0FKOWNRRlZDblJsYzNSamIyOXJhV1Z4QWxVR2QyOXlhMlZrY1FOekxnPT0KY2NhM2E4YmYwMWFk\nODcwMGFkNGI0ZDdiNzk0ZWM4ZjU=\n','2025-11-10 12:37:31'),('b4b8fe58434fe17f4cc44bfb1b1acdaf','Z0FKOWNRRW9WUkpmWVhWMGFGOTFjMlZ5WDJKaFkydGxibVJ4QWxVcFpHcGhibWR2TG1OdmJuUnlh\nV0l1WVhWMGFDNWlZV05yWlc1awpjeTVOYjJSbGJFSmhZMnRsYm1SeEExVU5YMkYxZEdoZmRYTmxj\nbDlwWkhFRWlnRUJWUTlrYW1GdVoyOWZiR0Z1WjNWaFoyVnhCVmdDCkFBQUFaVzV4Qm5VdQoyZTg3\nMWI4ZTcxMDlmYjgxZGNmZDgwMDNhMTMzMTQ5Mw==\n','2025-10-20 10:29:45'),('e32bf4531ba8adef8d206d540ac3bbe3','Z0FKOWNRRW9WUkpmWVhWMGFGOTFjMlZ5WDJKaFkydGxibVJ4QWxVcFpHcGhibWR2TG1OdmJuUnlh\nV0l1WVhWMGFDNWlZV05yWlc1awpjeTVOYjJSbGJFSmhZMnRsYm1SeEExVU5YMkYxZEdoZmRYTmxj\nbDlwWkhFRWlnRUJWUTlrYW1GdVoyOWZiR0Z1WjNWaFoyVnhCVmdDCkFBQUFaVzV4Qm5VdQoyZTg3\nMWI4ZTcxMDlmYjgxZGNmZDgwMDNhMTMzMTQ5Mw==\n','2025-10-17 09:39:00'),('173141e305eb72d93430baa52d72205b','Z0FKOWNRRW9WUTFmWVhWMGFGOTFjMlZ5WDJsa2NRS0tBUUZWRWw5aGRYUm9YM1Z6WlhKZlltRmph\nMlZ1WkhFRFZTbGthbUZ1WjI4dQpZMjl1ZEhKcFlpNWhkWFJvTG1KaFkydGxibVJ6TGsxdlpHVnNR\nbUZqYTJWdVpIRUVWUTlrYW1GdVoyOWZiR0Z1WjNWaFoyVnhCVmdDCkFBQUFaVzV4Qm5VdQoxYzQ3\nMGQyYWUyZTliZTkzOWMxNjhkOTJhMDkxNDk0Nw==\n','2025-10-16 15:58:28');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `empitemdefine`
--

DROP TABLE IF EXISTS `empitemdefine`;
CREATE TABLE `empitemdefine` (
  `ItemName` varchar(100) NOT NULL,
  `ItemType` varchar(20) default NULL,
  `Author_id` int(11) NOT NULL,
  `ItemValue` longtext,
  `Published` smallint(6) default NULL,
  PRIMARY KEY  (`ItemName`),
  KEY `empitemdefine_Author_id` (`Author_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `empitemdefine`
--

LOCK TABLES `empitemdefine` WRITE;
/*!40000 ALTER TABLE `empitemdefine` DISABLE KEYS */;
/*!40000 ALTER TABLE `empitemdefine` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `holidays`
--

DROP TABLE IF EXISTS `holidays`;
CREATE TABLE `holidays` (
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `HolidayID` int(11) NOT NULL auto_increment,
  `HolidayName` varchar(20) NOT NULL,
  `HolidayYear` smallint(6) default NULL,
  `HolidayMonth` smallint(6) default NULL,
  `HolidayDay` smallint(6) default NULL,
  `StartTime` date NOT NULL,
  `Duration` smallint(6) NOT NULL,
  `IsCycle` smallint(6) NOT NULL,
  `HolidayType` smallint(6) default NULL,
  `XINBIE` varchar(4) default NULL,
  `MINZU` varchar(50) default NULL,
  PRIMARY KEY  (`HolidayID`),
  UNIQUE KEY `HolidayName` (`HolidayName`,`StartTime`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `holidays`
--

LOCK TABLES `holidays` WRITE;
/*!40000 ALTER TABLE `holidays` DISABLE KEYS */;
INSERT INTO `holidays` VALUES (NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1,'New Year’s Day',2010,1,1,'2010-01-01',3,1,NULL,NULL,NULL),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,2,'National Day',2010,10,1,'2010-10-01',7,1,NULL,NULL,NULL);
/*!40000 ALTER TABLE `holidays` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `iclock`
--

DROP TABLE IF EXISTS `iclock`;
CREATE TABLE `iclock` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `sn` varchar(50) default NULL,
  `device_brand` int(11) NOT NULL,
  `device_type` int(11) NOT NULL,
  `last_activity` datetime default NULL,
  `trans_times` varchar(50) default NULL,
  `TransInterval` int(11) default NULL,
  `log_stamp` varchar(20) default NULL,
  `oplog_stamp` varchar(20) default NULL,
  `photo_stamp` varchar(20) default NULL,
  `alias` varchar(20) NOT NULL,
  `UpdateDB` varchar(10) default NULL,
  `fw_version` varchar(50) default NULL,
  `device_name` varchar(30) default NULL,
  `fp_count` int(11) default NULL,
  `transaction_count` int(11) default NULL,
  `user_count` int(11) default NULL,
  `main_time` varchar(20) default NULL,
  `max_user_count` int(11) default NULL,
  `max_finger_count` int(11) default NULL,
  `max_attlog_count` int(11) default NULL,
  `alg_ver` varchar(30) default NULL,
  `flash_size` varchar(10) default NULL,
  `free_flash_size` varchar(10) default NULL,
  `language` varchar(30) default NULL,
  `lng_encode` varchar(10) default NULL,
  `volume` varchar(10) default NULL,
  `dt_fmt` varchar(10) default NULL,
  `is_tft` varchar(5) default NULL,
  `platform` varchar(20) default NULL,
  `brightness` varchar(5) default NULL,
  `oem_vendor` varchar(30) default NULL,
  `city` varchar(50) default NULL,
  `AccFun` smallint(6) NOT NULL,
  `TZAdj` smallint(6) default NULL,
  `comm_type` smallint(6) NOT NULL,
  `agent_ipaddress` varchar(20) default NULL,
  `ipaddress` char(15) default NULL,
  `ip_port` int(11) default NULL,
  `subnet_mask` char(15) default NULL,
  `gateway` char(15) default NULL,
  `com_port` smallint(6) default NULL,
  `baudrate` smallint(6) default NULL,
  `com_address` smallint(6) default NULL,
  `area_id` int(11) default NULL,
  `comm_pwd` varchar(32) default NULL,
  `video_channel_count` int(11) default NULL,
  `acpanel_type` int(11) default NULL,
  `sync_time` tinyint(1) NOT NULL,
  `four_to_two` tinyint(1) NOT NULL,
  `video_login` varchar(20) default NULL,
  `fp_mthreshold` int(11) default NULL,
  `Fpversion` varchar(10) default NULL,
  `enabled` tinyint(1) NOT NULL,
  `max_comm_size` int(11) default NULL,
  `max_comm_count` int(11) default NULL,
  `realtime` tinyint(1) NOT NULL,
  `delay` int(11) default NULL,
  `encrypt` tinyint(1) NOT NULL,
  `dstime_id` int(11) default NULL,
  `is_elevator_device` tinyint(1) NOT NULL,
  `ele_extboard_count` smallint(6) default NULL,
  `relay_per_board` smallint(6) default NULL,
  PRIMARY KEY  (`id`),
  KEY `iclock_area_id` (`area_id`),
  KEY `iclock_dstime_id` (`dstime_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `iclock`
--

LOCK TABLES `iclock` WRITE;
/*!40000 ALTER TABLE `iclock` DISABLE KEYS */;
/*!40000 ALTER TABLE `iclock` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `iclock_dstime`
--

DROP TABLE IF EXISTS `iclock_dstime`;
CREATE TABLE `iclock_dstime` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `dst_name` varchar(20) NOT NULL,
  `mode` smallint(6) default NULL,
  `start_time` varchar(20) default NULL,
  `end_time` varchar(20) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `dst_name` (`dst_name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `iclock_dstime`
--

LOCK TABLES `iclock_dstime` WRITE;
/*!40000 ALTER TABLE `iclock_dstime` DISABLE KEYS */;
/*!40000 ALTER TABLE `iclock_dstime` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `iclock_oplog`
--

DROP TABLE IF EXISTS `iclock_oplog`;
CREATE TABLE `iclock_oplog` (
  `id` int(11) NOT NULL auto_increment,
  `SN` int(11) default NULL,
  `admin` int(11) NOT NULL,
  `OP` smallint(6) NOT NULL,
  `OPTime` datetime NOT NULL,
  `Object` int(11) default NULL,
  `Param1` int(11) default NULL,
  `Param2` int(11) default NULL,
  `Param3` int(11) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `SN` (`SN`,`OPTime`),
  KEY `iclock_oplog_SN` (`SN`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `iclock_oplog`
--

LOCK TABLES `iclock_oplog` WRITE;
/*!40000 ALTER TABLE `iclock_oplog` DISABLE KEYS */;
/*!40000 ALTER TABLE `iclock_oplog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `iclock_testdata`
--

DROP TABLE IF EXISTS `iclock_testdata`;
CREATE TABLE `iclock_testdata` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `dept_id` int(11) NOT NULL,
  `area_id` int(11) default NULL,
  PRIMARY KEY  (`id`),
  KEY `iclock_testdata_dept_id` (`dept_id`),
  KEY `iclock_testdata_area_id` (`area_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `iclock_testdata`
--

LOCK TABLES `iclock_testdata` WRITE;
/*!40000 ALTER TABLE `iclock_testdata` DISABLE KEYS */;
/*!40000 ALTER TABLE `iclock_testdata` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `iclock_testdata_admin_area`
--

DROP TABLE IF EXISTS `iclock_testdata_admin_area`;
CREATE TABLE `iclock_testdata_admin_area` (
  `id` int(11) NOT NULL auto_increment,
  `testdata_id` int(11) NOT NULL,
  `area_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `testdata_id` (`testdata_id`,`area_id`),
  KEY `iclock_testdata_admin_area_testdata_id` (`testdata_id`),
  KEY `iclock_testdata_admin_area_area_id` (`area_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `iclock_testdata_admin_area`
--

LOCK TABLES `iclock_testdata_admin_area` WRITE;
/*!40000 ALTER TABLE `iclock_testdata_admin_area` DISABLE KEYS */;
/*!40000 ALTER TABLE `iclock_testdata_admin_area` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `iclock_testdata_admin_dept`
--

DROP TABLE IF EXISTS `iclock_testdata_admin_dept`;
CREATE TABLE `iclock_testdata_admin_dept` (
  `id` int(11) NOT NULL auto_increment,
  `testdata_id` int(11) NOT NULL,
  `department_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `testdata_id` (`testdata_id`,`department_id`),
  KEY `iclock_testdata_admin_dept_testdata_id` (`testdata_id`),
  KEY `iclock_testdata_admin_dept_department_id` (`department_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `iclock_testdata_admin_dept`
--

LOCK TABLES `iclock_testdata_admin_dept` WRITE;
/*!40000 ALTER TABLE `iclock_testdata_admin_dept` DISABLE KEYS */;
/*!40000 ALTER TABLE `iclock_testdata_admin_dept` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `leaveclass`
--

DROP TABLE IF EXISTS `leaveclass`;
CREATE TABLE `leaveclass` (
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `LeaveID` int(11) NOT NULL auto_increment,
  `LeaveName` varchar(20) NOT NULL,
  `MinUnit` double NOT NULL,
  `Unit` smallint(6) NOT NULL,
  `RemaindProc` smallint(6) NOT NULL,
  `RemaindCount` smallint(6) NOT NULL,
  `ReportSymbol` varchar(4) NOT NULL,
  `Deduct` double default NULL,
  `Color` int(11) NOT NULL,
  `Classify` smallint(6) NOT NULL,
  `clearance` smallint(6) NOT NULL,
  `LeaveType` smallint(6) NOT NULL,
  PRIMARY KEY  (`LeaveID`)
) ENGINE=MyISAM AUTO_INCREMENT=7 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `leaveclass`
--

LOCK TABLES `leaveclass` WRITE;
/*!40000 ALTER TABLE `leaveclass` DISABLE KEYS */;
INSERT INTO `leaveclass` VALUES (NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1,'Sick',1,1,1,1,'B',0,3398744,0,0,1),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,2,'Personal',0.5,1,1,1,'G',0,16715535,0,0,2),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,3,'Maternity',0.5,1,1,1,'C',0,16715535,0,0,3),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,4,'Compassionate',1,1,1,1,'T',0,16744576,0,0,4),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,5,'Annual',1,1,1,1,'S',0,8421631,0,0,5),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,6,'Business Trip',1,1,1,1,'W',0,16715535,0,0,6);
/*!40000 ALTER TABLE `leaveclass` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `leaveclass1`
--

DROP TABLE IF EXISTS `leaveclass1`;
CREATE TABLE `leaveclass1` (
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `LeaveID` int(11) NOT NULL auto_increment,
  `LeaveName` varchar(20) NOT NULL,
  `MinUnit` double NOT NULL,
  `Unit` smallint(6) NOT NULL,
  `RemaindProc` smallint(6) NOT NULL,
  `RemaindCount` smallint(6) NOT NULL,
  `ReportSymbol` varchar(4) NOT NULL,
  `Deduct` double NOT NULL,
  `Color` int(11) NOT NULL,
  `Classify` smallint(6) NOT NULL,
  `LeaveType` smallint(6) NOT NULL,
  `Calc` longtext,
  PRIMARY KEY  (`LeaveID`)
) ENGINE=MyISAM AUTO_INCREMENT=1010 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `leaveclass1`
--

LOCK TABLES `leaveclass1` WRITE;
/*!40000 ALTER TABLE `leaveclass1` DISABLE KEYS */;
INSERT INTO `leaveclass1` VALUES (NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1000,'应到/实到',0.5,3,1,0,' ',0,0,0,3,NULL),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1001,'迟到',10,2,2,1,'>',0,0,0,3,'AttItem(minLater)'),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1002,'早退',10,2,2,1,'<',0,0,0,3,'AttItem(minEarly)'),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1003,'请假',1,1,1,1,'V',0,0,0,3,'if((AttItem(LeaveType1)>0) and (AttItem(LeaveType1)<999), \"AttItem(LeaveTime1), \"0)+if((AttItem(LeaveType2)>0) and (AttItem(LeaveType2)<999), \"AttItem(LeaveTime2), \"0)+if((AttItem(LeaveType3)>0) and (AttItem(LeaveType3)<999), \"AttItem(LeaveTime3), \"0)+if((AttItem(LeaveType4)>0) and (AttItem(LeaveType4)<999), \"AttItem(LeaveTime4), \"0)+if((AttItem(LeaveType5)>0) and (AttItem(LeaveType5)<999), \"AttItem(LeaveTime5), \"0)'),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1004,'旷工',0.5,3,1,0,'A',0,0,0,3,'AttItem(MinAbsent)'),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1005,'加班',1,1,1,1,'+',0,0,0,3,'AttItem(MinOverTime)'),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1008,'未签到',1,4,2,1,'[',0,0,0,2,'If(AttItem(CheckIn)\": null, \"If(AttItem(OnDuty)\": null, \"0, \"if(((AttItem(LeaveStart1)\": null) or (AttItem(LeaveStart1)>AttItem(OnDuty))) and AttItem(DutyOn), \"1, \"0)), \"0)'),(NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1009,'未签退',1,4,2,1,']',0,0,0,2,'If(AttItem(CheckOut)\": null, \"If(AttItem(OffDuty)\": null, \"0, \"if((AttItem(LeaveEnd1)\": null) or (AttItem(LeaveEnd1)<AttItem(OffDuty)), \"if((AttItem(LeaveEnd2)\": null) or (AttItem(LeaveEnd2)<AttItem(OffDuty)), \"if(((AttItem(LeaveEnd3)\": null) or (AttItem(LeaveEnd3)<AttItem(OffDuty))) and AttItem(DutyOff), \"1, \"0), \"0), \"0)), \"0)');
/*!40000 ALTER TABLE `leaveclass1` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `num_run`
--

DROP TABLE IF EXISTS `num_run`;
CREATE TABLE `num_run` (
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `Num_runID` int(11) NOT NULL auto_increment,
  `OLDID` int(11) default NULL,
  `Name` varchar(30) NOT NULL,
  `StartDate` date default NULL,
  `EndDate` date default NULL,
  `Units` smallint(6) NOT NULL,
  `Cyle` smallint(6) NOT NULL,
  PRIMARY KEY  (`Num_runID`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `num_run`
--

LOCK TABLES `num_run` WRITE;
/*!40000 ALTER TABLE `num_run` DISABLE KEYS */;
INSERT INTO `num_run` VALUES (NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1,-1,'Flexible shift','2025-10-06','2025-10-06',1,1);
/*!40000 ALTER TABLE `num_run` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `num_run_deil`
--

DROP TABLE IF EXISTS `num_run_deil`;
CREATE TABLE `num_run_deil` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `Num_runID` int(11) NOT NULL,
  `StartTime` time NOT NULL,
  `EndTime` time default NULL,
  `Sdays` smallint(6) NOT NULL,
  `Edays` smallint(6) default NULL,
  `SchclassID` int(11) default NULL,
  `OverTime` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `Num_runID` (`Num_runID`,`Sdays`,`StartTime`),
  KEY `num_run_deil_Num_runID` (`Num_runID`),
  KEY `num_run_deil_SchclassID` (`SchclassID`)
) ENGINE=MyISAM AUTO_INCREMENT=8 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `num_run_deil`
--

LOCK TABLES `num_run_deil` WRITE;
/*!40000 ALTER TABLE `num_run_deil` DISABLE KEYS */;
INSERT INTO `num_run_deil` VALUES (1,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1,'08:00:00','18:00:00',0,0,1,0),(2,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1,'08:00:00','18:00:00',1,1,1,0),(3,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1,'08:00:00','18:00:00',2,2,1,0),(4,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1,'08:00:00','18:00:00',3,3,1,0),(5,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1,'08:00:00','18:00:00',4,4,1,0),(6,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1,'08:00:00','18:00:00',5,5,1,0),(7,NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1,'08:00:00','18:00:00',6,6,1,0);
/*!40000 ALTER TABLE `num_run_deil` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `operatecmds`
--

DROP TABLE IF EXISTS `operatecmds`;
CREATE TABLE `operatecmds` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `Author_id` int(11) default NULL,
  `CmdContent` longtext NOT NULL,
  `CmdCommitTime` datetime NOT NULL,
  `commit_time` datetime default NULL,
  `CmdReturn` int(11) default NULL,
  `process_count` smallint(6) NOT NULL,
  `success_flag` smallint(6) NOT NULL,
  `receive_data` longtext,
  `cmm_type` smallint(6) NOT NULL,
  `cmm_system` smallint(6) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `operatecmds_Author_id` (`Author_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `operatecmds`
--

LOCK TABLES `operatecmds` WRITE;
/*!40000 ALTER TABLE `operatecmds` DISABLE KEYS */;
/*!40000 ALTER TABLE `operatecmds` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_area`
--

DROP TABLE IF EXISTS `personnel_area`;
CREATE TABLE `personnel_area` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `areaid` varchar(20) NOT NULL,
  `areaname` varchar(30) NOT NULL,
  `parent_id` int(11) default NULL,
  `remark` varchar(100) default NULL,
  PRIMARY KEY  (`id`),
  KEY `personnel_area_parent_id` (`parent_id`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `personnel_area`
--

LOCK TABLES `personnel_area` WRITE;
/*!40000 ALTER TABLE `personnel_area` DISABLE KEYS */;
INSERT INTO `personnel_area` VALUES (1,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'1','Area Name',NULL,NULL);
/*!40000 ALTER TABLE `personnel_area` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_cardtype`
--

DROP TABLE IF EXISTS `personnel_cardtype`;
CREATE TABLE `personnel_cardtype` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `cardtypecode` varchar(20) NOT NULL,
  `cardtypename` varchar(50) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `personnel_cardtype`
--

LOCK TABLES `personnel_cardtype` WRITE;
/*!40000 ALTER TABLE `personnel_cardtype` DISABLE KEYS */;
INSERT INTO `personnel_cardtype` VALUES (1,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'01','VIP card'),(2,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'02','Ordinary card');
/*!40000 ALTER TABLE `personnel_cardtype` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_empchange`
--

DROP TABLE IF EXISTS `personnel_empchange`;
CREATE TABLE `personnel_empchange` (
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `changeno` int(11) NOT NULL auto_increment,
  `UserID_id` int(11) NOT NULL,
  `changedate` datetime default NULL,
  `changepostion` int(11) default NULL,
  `oldvalue` longtext,
  `newvalue` longtext,
  `changereason` varchar(200) default NULL,
  `isvalid` tinyint(1) NOT NULL,
  `approvalstatus` int(11) NOT NULL,
  `remark` varchar(200) default NULL,
  PRIMARY KEY  (`changeno`),
  KEY `personnel_empchange_UserID_id` (`UserID_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `personnel_empchange`
--

LOCK TABLES `personnel_empchange` WRITE;
/*!40000 ALTER TABLE `personnel_empchange` DISABLE KEYS */;
/*!40000 ALTER TABLE `personnel_empchange` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_issuecard`
--

DROP TABLE IF EXISTS `personnel_issuecard`;
CREATE TABLE `personnel_issuecard` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `UserID_id` int(11) NOT NULL,
  `cardno` varchar(20) NOT NULL,
  `card_number` varchar(20) default NULL,
  `site_code` varchar(4) default NULL,
  `card_number_type` smallint(6) default NULL,
  `effectivenessdate` date default NULL,
  `isvalid` tinyint(1) NOT NULL,
  `cardpwd` varchar(20) default NULL,
  `failuredate` date default NULL,
  `cardstatus` varchar(20) NOT NULL,
  `issuedate` date default NULL,
  PRIMARY KEY  (`id`),
  KEY `personnel_issuecard_UserID_id` (`UserID_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `personnel_issuecard`
--

LOCK TABLES `personnel_issuecard` WRITE;
/*!40000 ALTER TABLE `personnel_issuecard` DISABLE KEYS */;
/*!40000 ALTER TABLE `personnel_issuecard` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_leavelog`
--

DROP TABLE IF EXISTS `personnel_leavelog`;
CREATE TABLE `personnel_leavelog` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `UserID_id` int(11) NOT NULL,
  `leavedate` date NOT NULL,
  `leavetype` int(11) NOT NULL,
  `reason` varchar(200) default NULL,
  `isReturnTools` tinyint(1) NOT NULL,
  `isReturnClothes` tinyint(1) NOT NULL,
  `isReturnCard` tinyint(1) NOT NULL,
  `isClassAtt` tinyint(1) NOT NULL,
  `isClassAccess` tinyint(1) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `personnel_leavelog_UserID_id` (`UserID_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `personnel_leavelog`
--

LOCK TABLES `personnel_leavelog` WRITE;
/*!40000 ALTER TABLE `personnel_leavelog` DISABLE KEYS */;
/*!40000 ALTER TABLE `personnel_leavelog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `schclass`
--

DROP TABLE IF EXISTS `schclass`;
CREATE TABLE `schclass` (
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `SchclassID` int(11) NOT NULL auto_increment,
  `SchName` varchar(20) NOT NULL,
  `StartTime` time NOT NULL,
  `EndTime` time NOT NULL,
  `LateMinutes` int(11) default NULL,
  `EarlyMinutes` int(11) default NULL,
  `CheckIn` smallint(6) NOT NULL,
  `CheckOut` smallint(6) NOT NULL,
  `CheckInTime1` time NOT NULL,
  `CheckInTime2` time NOT NULL,
  `CheckOutTime1` time NOT NULL,
  `CheckOutTime2` time NOT NULL,
  `Color` int(11) NOT NULL,
  `AutoBind` smallint(6) default NULL,
  `WorkDay` double default NULL,
  `IsCalcRest` int(11) default NULL,
  `StartRestTime` time default NULL,
  `EndRestTime` time default NULL,
  `StartRestTime1` time default NULL,
  `EndRestTime1` time default NULL,
  `shiftworktime` int(11) NOT NULL,
  `IsOverTime` smallint(6) NOT NULL,
  `OverTime` int(11) default NULL,
  PRIMARY KEY  (`SchclassID`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `schclass`
--

LOCK TABLES `schclass` WRITE;
/*!40000 ALTER TABLE `schclass` DISABLE KEYS */;
INSERT INTO `schclass` VALUES (NULL,'2025-10-06 15:12:44',NULL,'2025-10-06 15:12:44',NULL,NULL,0,1,'Flexible TimeTable','08:00:00','18:00:00',0,0,1,1,'00:01:00','23:00:00','01:00:00','23:59:00',16715535,1,1,0,NULL,NULL,NULL,NULL,480,1,0);
/*!40000 ALTER TABLE `schclass` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `setuseratt`
--

DROP TABLE IF EXISTS `setuseratt`;
CREATE TABLE `setuseratt` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `UserID_id` int(11) default NULL,
  `starttime` datetime NOT NULL,
  `endtime` datetime NOT NULL,
  `atttype` smallint(6) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `setuseratt_UserID_id` (`UserID_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `setuseratt`
--

LOCK TABLES `setuseratt` WRITE;
/*!40000 ALTER TABLE `setuseratt` DISABLE KEYS */;
/*!40000 ALTER TABLE `setuseratt` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `template`
--

DROP TABLE IF EXISTS `template`;
CREATE TABLE `template` (
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `templateid` int(11) NOT NULL auto_increment,
  `userid` int(11) NOT NULL,
  `Template` longtext NOT NULL,
  `FingerID` smallint(6) NOT NULL,
  `Valid` smallint(6) NOT NULL,
  `Fpversion` varchar(10) NOT NULL,
  `bio_type` smallint(6) NOT NULL,
  `SN` int(11) default NULL,
  `UTime` datetime default NULL,
  `BITMAPPICTURE` longtext,
  `BITMAPPICTURE2` longtext,
  `BITMAPPICTURE3` longtext,
  `BITMAPPICTURE4` longtext,
  `USETYPE` smallint(6) default NULL,
  `Template2` longtext,
  `Template3` longtext,
  PRIMARY KEY  (`templateid`),
  UNIQUE KEY `userid` (`userid`,`FingerID`,`Fpversion`),
  KEY `template_userid` (`userid`),
  KEY `template_SN` (`SN`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `template`
--

LOCK TABLES `template` WRITE;
/*!40000 ALTER TABLE `template` DISABLE KEYS */;
/*!40000 ALTER TABLE `template` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_of_run`
--

DROP TABLE IF EXISTS `user_of_run`;
CREATE TABLE `user_of_run` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `UserID` int(11) NOT NULL,
  `StartDate` date NOT NULL,
  `EndDate` date NOT NULL,
  `NUM_OF_RUN_ID` int(11) NOT NULL,
  `ISNOTOF_RUN` int(11) default NULL,
  `ORDER_RUN` int(11) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `UserID` (`UserID`,`NUM_OF_RUN_ID`,`StartDate`,`EndDate`),
  KEY `user_of_run_UserID` (`UserID`),
  KEY `user_of_run_NUM_OF_RUN_ID` (`NUM_OF_RUN_ID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `user_of_run`
--

LOCK TABLES `user_of_run` WRITE;
/*!40000 ALTER TABLE `user_of_run` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_of_run` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_speday`
--

DROP TABLE IF EXISTS `user_speday`;
CREATE TABLE `user_speday` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `UserID` int(11) NOT NULL,
  `StartSpecDay` datetime NOT NULL,
  `EndSpecDay` datetime default NULL,
  `DateID` int(11) NOT NULL,
  `YUANYING` varchar(100) default NULL,
  `Date` datetime default NULL,
  `audit_status` smallint(6) default NULL,
  `audit_reason` varchar(100) default NULL,
  `State` varchar(2) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `UserID` (`UserID`,`StartSpecDay`,`DateID`),
  KEY `user_speday_UserID` (`UserID`),
  KEY `user_speday_DateID` (`DateID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `user_speday`
--

LOCK TABLES `user_speday` WRITE;
/*!40000 ALTER TABLE `user_speday` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_speday` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_temp_sch`
--

DROP TABLE IF EXISTS `user_temp_sch`;
CREATE TABLE `user_temp_sch` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `UserID` int(11) NOT NULL,
  `ComeTime` datetime NOT NULL,
  `LeaveTime` datetime NOT NULL,
  `OverTime` int(11) NOT NULL,
  `Type` smallint(6) default NULL,
  `Flag` smallint(6) default NULL,
  `SchClassID` int(11) default NULL,
  `WorkType` smallint(6) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `UserID` (`UserID`,`ComeTime`,`LeaveTime`),
  KEY `user_temp_sch_UserID` (`UserID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `user_temp_sch`
--

LOCK TABLES `user_temp_sch` WRITE;
/*!40000 ALTER TABLE `user_temp_sch` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_temp_sch` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `userinfo`
--

DROP TABLE IF EXISTS `userinfo`;
CREATE TABLE `userinfo` (
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `userid` int(11) NOT NULL auto_increment,
  `badgenumber` varchar(20) NOT NULL,
  `defaultdeptid` int(11) default NULL,
  `name` varchar(24) default NULL,
  `lastname` varchar(20) default NULL,
  `Password` varchar(16) default NULL,
  `Card` varchar(20) NOT NULL,
  `card_number` varchar(20) default NULL,
  `site_code` varchar(4) default NULL,
  `card_number_type` smallint(6) default NULL,
  `Privilege` int(11) default NULL,
  `AccGroup` int(11) default NULL,
  `TimeZones` varchar(20) default NULL,
  `Gender` varchar(2) default NULL,
  `Birthday` date default NULL,
  `street` varchar(100) default NULL,
  `zip` varchar(6) default NULL,
  `ophone` varchar(20) default NULL,
  `FPHONE` varchar(20) default NULL,
  `pager` varchar(20) default NULL,
  `minzu` varchar(20) default NULL,
  `title` varchar(50) default NULL,
  `SSN` varchar(20) default NULL,
  `identitycard` varchar(20) default NULL,
  `UTime` datetime default NULL,
  `Hiredday` date default NULL,
  `VERIFICATIONMETHOD` smallint(6) default NULL,
  `State` varchar(50) default NULL,
  `City` varchar(50) default NULL,
  `Education` varchar(50) default NULL,
  `SECURITYFLAGS` smallint(6) default NULL,
  `ATT` tinyint(1) NOT NULL,
  `OverTime` tinyint(1) NOT NULL,
  `Holiday` tinyint(1) NOT NULL,
  `INLATE` smallint(6) default NULL,
  `OutEarly` smallint(6) default NULL,
  `Lunchduration` smallint(6) default NULL,
  `MVerifyPass` varchar(6) default NULL,
  `photo` varchar(200) default NULL,
  `SEP` smallint(6) default NULL,
  `OffDuty` smallint(6) default NULL,
  `DelTag` smallint(6) default NULL,
  `AutoSchPlan` smallint(6) default NULL,
  `MinAutoSchInterval` int(11) default NULL,
  `RegisterOT` int(11) default NULL,
  `morecard_group_id` int(11) default NULL,
  `set_valid_time` tinyint(1) NOT NULL,
  `acc_startdate` date default NULL,
  `acc_enddate` date default NULL,
  `acc_super_auth` smallint(6) default NULL,
  `ele_super_auth` smallint(6) default NULL,
  `delayed_door_open` tinyint(1) NOT NULL,
  `extend_time` smallint(6) default NULL,
  `birthplace` varchar(20) default NULL,
  `Political` varchar(20) default NULL,
  `contry` varchar(20) default NULL,
  `hiretype` int(11) default NULL,
  `email` varchar(50) default NULL,
  `firedate` date default NULL,
  `isatt` tinyint(1) NOT NULL,
  `homeaddress` varchar(100) default NULL,
  `emptype` int(11) default NULL,
  `bankcode1` varchar(50) default NULL,
  `bankcode2` varchar(50) default NULL,
  `isblacklist` int(11) default NULL,
  `selfpassword` varchar(20) default NULL,
  PRIMARY KEY  (`userid`),
  UNIQUE KEY `badgenumber` (`badgenumber`),
  KEY `userinfo_defaultdeptid` (`defaultdeptid`),
  KEY `userinfo_morecard_group_id` (`morecard_group_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `userinfo`
--

LOCK TABLES `userinfo` WRITE;
/*!40000 ALTER TABLE `userinfo` DISABLE KEYS */;
/*!40000 ALTER TABLE `userinfo` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `userinfo_attarea`
--

DROP TABLE IF EXISTS `userinfo_attarea`;
CREATE TABLE `userinfo_attarea` (
  `id` int(11) NOT NULL auto_increment,
  `employee_id` int(11) NOT NULL,
  `area_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `employee_id` (`employee_id`,`area_id`),
  KEY `userinfo_attarea_employee_id` (`employee_id`),
  KEY `userinfo_attarea_area_id` (`area_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `userinfo_attarea`
--

LOCK TABLES `userinfo_attarea` WRITE;
/*!40000 ALTER TABLE `userinfo_attarea` DISABLE KEYS */;
/*!40000 ALTER TABLE `userinfo_attarea` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `useruusedsclasses`
--

DROP TABLE IF EXISTS `useruusedsclasses`;
CREATE TABLE `useruusedsclasses` (
  `id` int(11) NOT NULL auto_increment,
  `UserId` int(11) NOT NULL,
  `SchId` int(11) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `UserId` (`UserId`,`SchId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `useruusedsclasses`
--

LOCK TABLES `useruusedsclasses` WRITE;
/*!40000 ALTER TABLE `useruusedsclasses` DISABLE KEYS */;
/*!40000 ALTER TABLE `useruusedsclasses` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vid_channel`
--

DROP TABLE IF EXISTS `vid_channel`;
CREATE TABLE `vid_channel` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `device_id` int(11) default NULL,
  `channel_no` smallint(5) unsigned default NULL,
  `channel_name` varchar(30) default NULL,
  `enabled` tinyint(1) NOT NULL,
  `reader_id` int(11) default NULL,
  `map_id` int(11) default NULL,
  PRIMARY KEY  (`id`),
  KEY `vid_channel_device_id` (`device_id`),
  KEY `vid_channel_reader_id` (`reader_id`),
  KEY `vid_channel_map_id` (`map_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `vid_channel`
--

LOCK TABLES `vid_channel` WRITE;
/*!40000 ALTER TABLE `vid_channel` DISABLE KEYS */;
/*!40000 ALTER TABLE `vid_channel` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vid_mapchannelpos`
--

DROP TABLE IF EXISTS `vid_mapchannelpos`;
CREATE TABLE `vid_mapchannelpos` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `map_channel_id` int(11) default NULL,
  `map_id` int(11) default NULL,
  `width` double default NULL,
  `left` double default NULL,
  `top` double default NULL,
  PRIMARY KEY  (`id`),
  KEY `vid_mapchannelpos_map_channel_id` (`map_channel_id`),
  KEY `vid_mapchannelpos_map_id` (`map_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `vid_mapchannelpos`
--

LOCK TABLES `vid_mapchannelpos` WRITE;
/*!40000 ALTER TABLE `vid_mapchannelpos` DISABLE KEYS */;
/*!40000 ALTER TABLE `vid_mapchannelpos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vis_place`
--

DROP TABLE IF EXISTS `vis_place`;
CREATE TABLE `vis_place` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `code` varchar(30) default NULL,
  `name` varchar(50) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `vis_place`
--

LOCK TABLES `vis_place` WRITE;
/*!40000 ALTER TABLE `vis_place` DISABLE KEYS */;
/*!40000 ALTER TABLE `vis_place` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vis_reason`
--

DROP TABLE IF EXISTS `vis_reason`;
CREATE TABLE `vis_reason` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `code` varchar(30) default NULL,
  `reason` varchar(50) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `reason` (`reason`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `vis_reason`
--

LOCK TABLES `vis_reason` WRITE;
/*!40000 ALTER TABLE `vis_reason` DISABLE KEYS */;
/*!40000 ALTER TABLE `vis_reason` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vis_report`
--

DROP TABLE IF EXISTS `vis_report`;
CREATE TABLE `vis_report` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `visited_pin` varchar(20) default NULL,
  `visited_firstname` varchar(24) default NULL,
  `visited_lastname` varchar(24) default NULL,
  `visited_dept` varchar(100) default NULL,
  `visited_phone` varchar(20) default NULL,
  `visitor_pin` varchar(9) default NULL,
  `visitor_firstname` varchar(24) default NULL,
  `visitor_lastname` varchar(24) default NULL,
  `gender` varchar(10) default NULL,
  `homeaddress` varchar(100) default NULL,
  `cert_type` varchar(50) default NULL,
  `cert_number` varchar(20) default NULL,
  `card` varchar(20) default NULL,
  `visitor_company` varchar(50) default NULL,
  `visit_reason` varchar(100) default NULL,
  `visitor_number` int(11) default NULL,
  `enter_time` datetime default NULL,
  `exit_time` datetime default NULL,
  `entrance` varchar(50) default NULL,
  `exit_place` varchar(50) default NULL,
  `visit_state` varchar(20) default NULL,
  `carried_goods` longtext,
  `photo` varchar(50) default NULL,
  `enter_photo` varchar(50) default NULL,
  `exit_photo` varchar(50) default NULL,
  `visitor_form` varchar(30) default NULL,
  `car_number` varchar(15) default NULL,
  `park_number` varchar(15) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `vis_report`
--

LOCK TABLES `vis_report` WRITE;
/*!40000 ALTER TABLE `vis_report` DISABLE KEYS */;
/*!40000 ALTER TABLE `vis_report` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vis_reservation`
--

DROP TABLE IF EXISTS `vis_reservation`;
CREATE TABLE `vis_reservation` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `visited_emp_id` int(11) NOT NULL,
  `visitor_firstname` varchar(24) default NULL,
  `visitor_lastname` varchar(24) default NULL,
  `visitor_company` varchar(24) default NULL,
  `visit_reason_id` int(11) default NULL,
  `visit_date` date default NULL,
  `remark` varchar(200) default NULL,
  PRIMARY KEY  (`id`),
  KEY `vis_reservation_visited_emp_id` (`visited_emp_id`),
  KEY `vis_reservation_visit_reason_id` (`visit_reason_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `vis_reservation`
--

LOCK TABLES `vis_reservation` WRITE;
/*!40000 ALTER TABLE `vis_reservation` DISABLE KEYS */;
/*!40000 ALTER TABLE `vis_reservation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vis_visitor`
--

DROP TABLE IF EXISTS `vis_visitor`;
CREATE TABLE `vis_visitor` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `visitor_id` int(11) default NULL,
  `cert_type` smallint(6) default NULL,
  `cert_number` varchar(20) default NULL,
  `visitor_company` varchar(24) default NULL,
  `visit_reason_id` int(11) default NULL,
  `visitor_number` int(11) default NULL,
  `visit_state` int(11) default NULL,
  `enter_time` datetime default NULL,
  `exit_time` datetime default NULL,
  `entrance_id` int(11) default NULL,
  `exit_place_id` int(11) default NULL,
  `cert_photo` longtext,
  `capture_photo` longtext,
  `car_number` varchar(15) default NULL,
  `park_number` varchar(15) default NULL,
  `carried_goods` longtext,
  `visitor_form` varchar(30) default NULL,
  `visited_emp_id` int(11) default NULL,
  `has_alarmed` tinyint(1) NOT NULL,
  `has_visited` tinyint(1) NOT NULL,
  `exit_registered` tinyint(1) NOT NULL,
  `return_card` int(11) default NULL,
  PRIMARY KEY  (`id`),
  KEY `vis_visitor_visitor_id` (`visitor_id`),
  KEY `vis_visitor_visit_reason_id` (`visit_reason_id`),
  KEY `vis_visitor_entrance_id` (`entrance_id`),
  KEY `vis_visitor_exit_place_id` (`exit_place_id`),
  KEY `vis_visitor_visited_emp_id` (`visited_emp_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `vis_visitor`
--

LOCK TABLES `vis_visitor` WRITE;
/*!40000 ALTER TABLE `vis_visitor` DISABLE KEYS */;
/*!40000 ALTER TABLE `vis_visitor` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `worktable_groupmsg`
--

DROP TABLE IF EXISTS `worktable_groupmsg`;
CREATE TABLE `worktable_groupmsg` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `msgtype_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `worktable_groupmsg_msgtype_id` (`msgtype_id`),
  KEY `worktable_groupmsg_group_id` (`group_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `worktable_groupmsg`
--

LOCK TABLES `worktable_groupmsg` WRITE;
/*!40000 ALTER TABLE `worktable_groupmsg` DISABLE KEYS */;
/*!40000 ALTER TABLE `worktable_groupmsg` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `worktable_instantmsg`
--

DROP TABLE IF EXISTS `worktable_instantmsg`;
CREATE TABLE `worktable_instantmsg` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `monitor last time` datetime default NULL,
  `msgtype_id` int(11) NOT NULL,
  `content` longtext,
  PRIMARY KEY  (`id`),
  KEY `worktable_instantmsg_msgtype_id` (`msgtype_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `worktable_instantmsg`
--

LOCK TABLES `worktable_instantmsg` WRITE;
/*!40000 ALTER TABLE `worktable_instantmsg` DISABLE KEYS */;
/*!40000 ALTER TABLE `worktable_instantmsg` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `worktable_msgtype`
--

DROP TABLE IF EXISTS `worktable_msgtype`;
CREATE TABLE `worktable_msgtype` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `msgtype_name` varchar(50) NOT NULL,
  `msgtype_value` varchar(20) NOT NULL,
  `msg_keep_time` int(11) NOT NULL,
  `msg_ahead_remind` int(11) NOT NULL,
  `type` varchar(2) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `worktable_msgtype`
--

LOCK TABLES `worktable_msgtype` WRITE;
/*!40000 ALTER TABLE `worktable_msgtype` DISABLE KEYS */;
INSERT INTO `worktable_msgtype` VALUES (1,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'System','9',1,0,'-1'),(2,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'Attendance','8',1,0,'-1'),(3,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'Access Control','7',1,0,'-1'),(4,NULL,'2025-10-06 15:12:43',NULL,'2025-10-06 15:12:43',NULL,NULL,0,'Personnel','6',1,0,'-1');
/*!40000 ALTER TABLE `worktable_msgtype` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `worktable_usrmsg`
--

DROP TABLE IF EXISTS `worktable_usrmsg`;
CREATE TABLE `worktable_usrmsg` (
  `id` int(11) NOT NULL auto_increment,
  `change_operator` varchar(30) default NULL,
  `change_time` datetime default NULL,
  `create_operator` varchar(30) default NULL,
  `create_time` datetime default NULL,
  `delete_operator` varchar(30) default NULL,
  `delete_time` datetime default NULL,
  `status` smallint(6) NOT NULL,
  `user_id` int(11) default NULL,
  `msg_id` int(11) default NULL,
  `readtype` varchar(20) default NULL,
  PRIMARY KEY  (`id`),
  KEY `worktable_usrmsg_user_id` (`user_id`),
  KEY `worktable_usrmsg_msg_id` (`msg_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `worktable_usrmsg`
--

LOCK TABLES `worktable_usrmsg` WRITE;
/*!40000 ALTER TABLE `worktable_usrmsg` DISABLE KEYS */;
/*!40000 ALTER TABLE `worktable_usrmsg` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-11-21 10:20:49
