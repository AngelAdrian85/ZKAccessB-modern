# -*- coding: utf-8 -*-
# *****一些静态的常量，根据不同的系统自己写一份不同的参数，不在
# ****不在通过mysite.att in ...这种方式来做复杂的判断
# 默认为ZKECO的配置
import const
from django.utils.translation import ugettext_lazy as _

const.BROWSER_TITLE = _("ZKECO 时间&安全管理平台")  # 登入页面的浏览器标题
# _(u"门禁管理系统")
# _("ZKAccess4.5 门禁管理系统")
# _("ZKAccess5.0 门禁管理系统")
# _("时间&安全管理平台")
# _("ZKECO 时间&安全管理平台")
# _("门禁管理系统" )
# _("ZKAccess5.0 门禁管理系统")
# _("考勤管理系统" )
# _("ZKTime8.0 考勤管理系统")

# const.SELF_LOGIN="" const.NORMAL_LOGIN="displayN"标示要员工自助
# const.SELF_LOGIN="displayN" const.NORMAL_LOGIN="" 标示不需要员工自助
const.SELF_LOGIN = ""  # 员工自助登入
const.NORMAL_LOGIN = "displayN"  # 正常登入
