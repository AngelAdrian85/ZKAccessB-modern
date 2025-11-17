var surl=$("#id_surl").val();
var dbapp_url=$("#id_dbapp_url").val();

function init_page(){
    var mmli=$(".help_more_list").find("li");
    var mmw=0;
    for(i=0;i<=mmli.length-1;i++){
        if($(mmli[i]).width()>mmw)
        mmw=$(mmli[i]).width();
    }
    $(".help_more_list").css({width:mmw});
    $(".help_more_list>li").css({width:"100%"});
    $(".help_more_list").bgiframe();
            
    $("#id_copy_right").click(function(){
        //获取license信息
        var upk = "";
        var license_info = "";
        var trial = 0;
        var acc_license_info = "";
        $.ajax({
            type: "GET",
            async: false,
            dataType: "json",
            url: '/'+surl+'data/GetLicenseInfo',
            success:function(data)
            {
                upk = data["upk"];//.split('"');
                trial = data["trial"];
                video_version = data["video"];
                license_info = data["license_info"];
                if(trial != 0)// 试用版
                {
                    var split_str = "<br/>";
                    acc_end_length = license_info.indexOf(split_str);
                    var split_length = acc_end_length+split_str.length;
                    acc_license_info = license_info.substring(0, split_length);
                    license_info = license_info.substring(split_length, license_info.length);
                }
            }
        });
        //alert(acc_license_info);
        //alert(license_info);
        var sys_type = $("#id_sys_type").val();//zkeco zkaccess zktime
        var is_oem = $("#id_oem").val();
        var is_zkaccess_att = $("#id_zkaccess_att").val();
        var is_zkaccess_5to4 = $("#id_zkaccess_5to4").val();
        var title_name = "ZKECO";
        var att_name = "ZKTime";
        var acc_name = "ZKAccess";
        var version = "";
        var version_name = "ZKSoftware Inc";
        var version_logo = "";
        var oem_class = "";
        var att_version = "8.2.0";

        var acc_version = "5.3.13704";
        
        //var build_id = "XS20111123-6-01";
        
        if(sys_type === 'zkaccess')
        {
            if(is_oem == "True")
            {
                title_name = "Access";
                acc_name = "Access";
                version_name = "";
                oem_class = "_oem";
            }
            else
            {
                title_name = "ZKAccess";
            }
            version = acc_name + ": " + acc_version + "<br />";
        }
        else if(sys_type === 'zktime')
        {
            if(is_oem == "True")
            {
                title_name = "Attendance";
                att_name = "Attendance";
                version_name = "";
                oem_class = "_oem";
            }
            else
            {
                title_name = "ZKTime";
            }
            version = att_name + ": " + att_version + "<br />";
        }
        else
        {   
            if(is_zkaccess_att == "True")
            {
                if(is_oem == "True")
                {
                    title_name = "Access";
                    acc_name = "Access";
                    version_name = "";
                    oem_class = "_oem";
                }
                else
                {
                    title_name = "ZKAccess";
                    version_name = "";
                }
                version = acc_name + ": " + acc_version + "<br />";
            }
            else
            {
                if(is_oem == "True")
                {
                    title_name = "ECO";
                    att_name = "Attendance";
                    acc_name = "Access";
                    version_name = "";
                    oem_class = "_oem";
                }
                version = title_name + ": 3000<br />"
                    + att_name+": " + att_version + "<br />"
                    + acc_name+": " + acc_version + "<br />";
            }
        }
        
        var license_info_title = "";
        if(trial == 0)
        {
            license_info_title = gettext("正式版许可");
        }
        else
        {
            license_info_title = gettext("试用版许可");
        }
        var vbox= $("<div class='version_box'>"
                + "<div class='version_content_box"+oem_class+"'>"
                    + "<div class='version_details_box'><span>"
                        + gettext("版本号")+":</span><br />"							
                        + version
                       // + gettext("产品ID")+":</span><br />"							
                       // + build_id+"<br/><span>"
                        + acc_license_info +"<span>"
                        + license_info_title+":</span><br />"	
                        + license_info+"<br/><span>"
                        + gettext("本系统建议使用浏览器")
                        + ":</span><br />Internet Explorer 8.0+/Firefox 3.6+<br /><span>"
                        + gettext("显示器分辨率")
                        + ":</span><br />1024×768 "
                        + gettext("及以上像素")+"<br /><span>"
                        + gettext("软件运行环境")
                        + ":</span><br />Windows XP/2003/7 MySQL"
                        + "/MS SQL Server"
                    + "</div>"
                    + "<div class='version_copyRight'>Copyright &copy; "+$("#id_current_year").val()+" "+version_name+".</div>"
                    + "</div>"
                + "</div>");
        vbox.dialog({title:gettext("关于") +" "+ title_name});
    });

    $("#id_page_load").bgiframe();
    $("#eMeng").bgiframe();
    var var_app_menu=$("#id_app_menu");
    //菜单行超过宽度产生折行时，把最后一个菜单项放到下拉列表中去
    //IE7: width()=803
    //IE8: width()=867
    //暂时缩小宽度 --by huangjs 20120309
    //while(var_app_menu.width()>825)
    var app_menu_width = 800;
    if($("html").attr("lang") == "es")
    {
    	app_menu_width = 726;
    }
    while(var_app_menu.width()>app_menu_width)    
    {
       var var_li=$("li.tabs_li:last", var_app_menu);
       $(".menu_more").prepend(var_li);
    }					
    if($(".menu_more").find("li").length==0){
        $("#nav").hide();
    }
    else{
        $("#nav").show();
    }
    var mli=$(".menu_more").find("a");
    var mw=0;
    for(i=0;i<=mli.length-1;i++){
        if($(mli[i]).width()>mw)
        mw=$(mli[i]).width();
    }
    mw=mw + 20;
    $(".menu_more").css({width:mw});
    $(".menu_more>li").css({width:"100%"});
       //根目录
        document.title=$("#id_browse_title").val();
    //console.log("on page load start");
    $("#id_page_load").hide();
    if($.browser.msie){
        document.execCommand("BackgroundImageCache", false, true);
    }

      page_load_effects("/"+surl+"accounts/login/",$("#id_gz"),$("#id_page_load"));
    //处理菜单
      $("#id_true_app li").each(function(){
        if($(".app_"+$(this).attr("name")).length>0){//如果在别的地方配置了这个应用的app_app_name样式,就删除之
            $(this).remove();
        }
    });
    //我的工作台
    $("#id_worktable").attr("href",dbapp_url+"worktable/");	
    $('.nav li').sfHover();
    $("#id_btn_logout").click(function(){
        if(confirm(gettext('确定注销系统?'))){
                $.ajax({
                    type:"POST",
                    url:$(this).attr("ref"),
                    success:function(msg){
                        if(msg=="ok"){
                            window.location.replace("/"+surl+"accounts/login/");
                        }
                    }
                });
        }
    })
    $("#id_btn_option,#id_btn_changePW").click(function(){
        var a_this=this;
        var btn_values=[gettext("确定"),gettext("取消")]
        if($(this).attr("btn_values")){
            btn_values=$(this).attr("btn_values").split("__");
        }
        var d=new Date();
        var href=$(this).attr("ref")+"?stamp="+d.getTime();
        var next_checking="ok";
        $.ajax({
            url:href,
            type:"GET",
            success:function(msg){
                if($("#id_opt_message").length==0){
                    $("body").append("<div id='id_opt_message'></div>");
                }
                var msg_dialog=$("#id_opt_message");
                msg_dialog.append(msg);
                render_widgets(msg_dialog);
                if($("#ret_info",msg_dialog).length==0){
                    msg_dialog.append("<div id='id_ret_info' class='ret_info'></div>"); 
                }
                
                var btns='<div class="btns_class"><button class="btn" id="id_OK" type="button">'+btn_values[0]+'</button>'
                        +'<button class="btn" id="id_Cancel" type="button">'+btn_values[1]+'</button></div>'
                var $form=msg_dialog.find("form");
                $form.find("input[type!=hidden]").keydown(
                    function(event){
                        if(event.keyCode==13)
                        {
                            msg_dialog.find("#id_OK").click();
                        }
                });
               
                
                $("#id_new_password1").attr("maxlength","18"); 
                $("#id_new_password2").attr("maxlength","18");//修改密码 限制位数

                $form.append(btns);
                $("#id_span_title",msg_dialog).find("span:not(.icon_SiteMap)").remove();
                msg_dialog.find("#id_Cancel").click(function(){
                    $("#id_close",msg_dialog).click();
					$(".bgiframe78").remove();
                });
                msg_dialog.find("#id_OK").click(function(){
                    var pwd1=$("#id_new_password1").val();
                    var pwd2=$("#id_new_password2").val();
                    if (pwd1)
                    {   
                        next_checking="ok";
                        if((pwd1[0]==" ") || (pwd2[0]==" "))
                        {
                            alert(gettext('首字符不能为空!'));
                            next_checking="no";
                            return false;
                        
                        }
                        if (pwd1.length < 5 ||pwd2.length <5 )
                        {
                            alert(gettext('密码长度必须大于4位!'));
                            next_checking="no";
                            return false;
                        }
                    }
                    if($form.valid()&&next_checking=="ok"){
                        $form.ajaxSubmit({ 
                            url:href, 
                            dataType:"html", 
                            async:false, 
                            success:function(msgback){ 
                                if(msgback.indexOf('{ Info:"OK" }')!=-1){
                                    $("#id_close",msg_dialog).click();
									$(".bgiframe78").remove();
                                    if($(a_this).attr("id")=="id_btn_option"){
                                        window.location.reload();
                                    }
                                }else{
                                    var ret_div=$("#id_ret_info",msg_dialog);
                                    ret_div.html($(msgback).find("ul.errorlist").eq(0));
                                    if($(a_this).attr("class")=="btn_changePW"){
                                        var $inputs=msg_dialog.find("input[type!=hidden]");
                                        $inputs.eq(0).select();
                                        $inputs.not(":first").val("");
                                    }
                                }
                            }
                        });
                    }
                });
                
                msg_dialog.dialog({
                    title:$(a_this).text(),
                    on_load:function(obj){
                        obj.target.getOverlay().find("input[type!=hidden]:first").focus().select();
						if($.browser.msie && $.browser.version > 6){
							$("#overlay").prepend("<iframe class='bgiframe78' frameborder='0' style='filter: Alpha(Opacity=\"0\"); position:absolute; width:"+$("#overlay").width()+"px;height:"+$("#overlay").height()+"px;z-index:-1'></iframe>")
						}
                }});
				
                
            },
            error:function (XMLHttpRequest, textStatus, errorThrown) {
                alert(gettext("服务器处理数据失败，请重试！错误码：-616"));//服务器加载数据失败,请重试!
            }
            
        });
    });
}


function OnCommError() {
    var d=new Date()
    getUrl='/'+surl+'iaccess/comm_error_msg/';
    $.ajax({ 
        type:"GET", 
        url:getUrl, 
        dataType:"json", 
        async:true, 
        success:function(rtlog)
        {
            rtlisthtml = ""
            for(var index in rtlog.data) 
            {
                datas = rtlog.data[index];
                if (datas != undefined)
                {
                    rtlisthtml += "<P align=left><a target='_blank' href='/"+surl+"iclock/DevRTMonitorPage/'><font color=#FF0000>" + datas.devname + gettext('通讯失败') + "</font></a></P>"
                }
            }
            $("#id_comm_error marquee").empty();
            $("#id_comm_error marquee").prepend(rtlisthtml);
           // window.setTimeout('OnCommError()', 10000)//等*秒执行刷新函数原来20s
        }
    });
}
function init_iaccess(){
    //window.setTimeout('OnCommError()', 1000);
}