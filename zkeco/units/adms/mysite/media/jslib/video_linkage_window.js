/**
 *  jQuery Windows Engine Plugin
 *@requires jQuery v1.2.6
 *  http://www.socialembedded.com/labs
 *  Download by http://www.jb51.net
 *  Copyright (c) 王金峰 Darcy ZKTeco Inc.
 *  Create date: 2012.3.13
 *  Version: 1.0


$win_show_div用来打开新窗口的div，默认隐藏。
*/
var pop_video_count = 0;//该变量用于保证最后一个弹出的视频窗口不被提前关闭----by liangm 2012-04-11
var g_video_brand = 0;
function init_video_window($win_show_div, win_title, win_content, win_width, win_height, win_posx, win_posy, creat_new_window)
{
    //$("#id_window_container").empty();//只保留一个
//    $(".window-closeButton").each(function(){
//        $(this).click();
//    });
	if(creat_new_window == 0)
    {
        $win_show_div.newWindow({
            windowTitle: win_title,
            content: '<div id="id_vid_loading">'+gettext("视频加载中，请稍侯...")+'</div>'+win_content,
            windowType: "video",
            width: win_width, height: win_height,
            //以页面的左上角为坐标原点，posx为距离原点横轴的坐标。posy为距离原点纵轴的坐标。-darcy20120508
            posx: win_posx,
            posy: win_posy
        });
    }
    $("#id_window_container").hide();
    $win_show_div.click();
    
    //$(".window-container").hide();
}

/*
$vid_ocx_div实为存放ocx的div
*/
function check_init_vid_ocx($vid_ocx_div, ocx_obj, ocx_id)
{

	$vid_ocx_div.empty();
    $vid_ocx_div.append(ocx_obj);
    if(document.getElementById(ocx_id).object == null)
    {
        $("#id_window_container").empty();//避免失败时弹出框
        alert(gettext("控件初始化失败，请确定视频设备类型是否选择正确或重装控件！"));
        return false;               
    }
    else
    {
        return true;
    }
}

/*
注册成功返回user_id
注册失败返回false，前端可直接判断
check_init_ocx和vid_login不能合并的原因之一是，会有冗余参数
*/
function vid_login(vid_hkocx_obj, last_vid_ip, vid_ip, vid_port, last_user_id, vid_user, vid_pwd, video_brand)
{
    //vid_hkocx_obj = document.getElementById(ocx_id);
    var user_id = null;
    var need_re_login = true;//需要重新login
    if(last_vid_ip == vid_ip && last_user_id != -1)
    {
        need_re_login = false;
    }
    else
    {
        if(video_brand == 200)
        {
            try
            {
                //alert("-last_user_id="+last_user_id)
                if(vid_hkocx_obj.SetUserID(parseInt(last_user_id)))
                {
                    vid_hkocx_obj.Logout();//登录前先注销。
                }
            }
            catch(e)//parseInt(null)
            {//alert("--last_user_id="+last_user_id+' -user_id='+user_id)
                vid_hkocx_obj.Logout();//登录前先注销。
            }
        }
        else if(video_brand == 300)
        {
        	try
            {
        		//vid_hkocx_obj.LogoutDevice();由于目前采用的是大华新控件，此处需屏蔽，否则视频联动时，浏览器崩溃. ---------by liangm 20131002
        	}
            catch(e)
            {
            }
        }
    }

    if(need_re_login)
    {
        var count = 0;
        while(count<2)
        {
            //vid_hkocx_obj.Logout();//登录前先注销。
            if(video_brand == 200)
            {
                user_id = vid_hkocx_obj.Login(vid_ip, vid_port, vid_user, vid_pwd);//返回当前登录的用户数，-1代表失败
            }
            else if(video_brand == 101)
            {
                user_id = vid_hkocx_obj.SetUrl(vid_ip,vid_port,12,vid_user,vid_pwd);
            }
            else if(video_brand == 300)
            {
            	user_id = vid_hkocx_obj.LoginDeviceEx(vid_ip, vid_port, vid_user, vid_pwd, 0);//大华dvr登录失败，返回值为0
            	if(user_id == 0)
            	{
            		user_id = -1;
            	}
            }
            if(user_id >= 0)
            {
                break;
            }
            else
            {
                count += 1;
            }
        }
    }
    else
    {
        user_id = last_user_id;
    }
    //alert("-------last_user_id="+last_user_id+"  --------user_id="+user_id);
    if(user_id < 0)
    {
        $("#id_window_container").hide();//避免失败时弹出框
        var last_error = null;
        if(video_brand == 200)
        {
        	try
        	{
	        	last_error = vid_hkocx_obj.GetLastError();
	            vid_hkocx_obj.Logout();
	            //vid_hkocx_obj.ClearOCX();
        	}
        	catch(e)
        	{
        		last_error = 7;
        	}
            
        }
        else if(video_brand == 101)
        {
            last_error = user_id;
        }
        else if(video_brand == 300)
        {
        	lass_error = user_id;
        }
        if(last_error != 0)
        {
            try
            {
                alert(gettext("视频服务器登录失败，请确认后重试！原因：")+gettext("HIKVISION_ERROR_"+last_error));
            }
            catch(e)
            {
                alert(gettext("视频服务器登录失败，请确认后重试！错误码：")+last_error);
            }
        }
        
    }
    return user_id;
}

//视频预览
function vid_realplay_record(vid_hkocx_obj, vid_channel, vid_time, vid_id, user_id, video_brand)
{
    //alert(user_id)
    //预览
    var ret_real_play = true;
    var play_count = 0;
    g_video_brand = video_brand;
    if(video_brand == 200)
    {
        vid_hkocx_obj.SetPlayWndType(0);//调整画面。0 - 充满， 1 - 4:3模式， 2 - 16:9模式
    }
    if(last_vid_id == 0 || last_vid_id != vid_id)
    {//alert(33);
        while(play_count < 3)
        {//alert(44);
            if(video_brand == 200)
            {
                vid_hkocx_obj.StopRealPlay();//预览前，先停止预览
                ret_real_play = vid_hkocx_obj.StartRealPlay(vid_channel, 0, 0);//0代表主码流，1代表次码流
            }
            else if(video_brand == 101)
            {
                ret_real_play = vid_hkocx_obj.Play();
                if(ret_real_play == -1)
                {
                	ret_real_play = false;
                }
				else
				{
					ret_real_play = true;
				}
            }
            else if(video_brand == 300)
            {
            	ret_real_play = vid_hkocx_obj.ConnectRealVideo(vid_channel,1);
            }
            if(ret_real_play == true)
            {
                break;
            }
            else
            {
                play_count += 1;
            }
        }
    }
//    else
//    {   
//        alert("33333333 "+" last_vid_id="+last_vid_id+" vid_id="+vid_id)
//    }
	if(ret_real_play == true)
	{
        pop_video_count += 1;
        last_vid_id = vid_id;
		$("#id_vid_loading").hide();
    	$("#id_window_container").show();
		window.setTimeout('if(pop_video_count<=1){if(g_video_brand == 200){vid_hkocx_obj.StopRealPlay();vid_hkocx_obj.Logout();} else if(g_video_brand == 101){vid_hkocx_obj.Stop();} else if(g_video_brand == 300){vid_hkocx_obj.LogoutDevice();} $("#id_monitor_events").focus();$("#id_window_container").hide();last_vid_id = 0;last_vid_ip = "";} pop_video_count-=1;', vid_time*1000);//关闭视频预览
	}
    else
    {
        $("#id_window_container").hide();
        last_vid_brand = 0;
        last_vid_id = 0;
        var last_error = null;
        if(video_brand == 200)
        {
            last_error = vid_hkocx_obj.GetLastError();
            vid_hkocx_obj.Logout();
            //vid_hkocx_obj.ClearOCX();
        }
        else if(video_brand == 101)
        {
            if(ret_real_play == false)
            {
            	last_error = -1;
            }
        }
        else if(video_brand == 300)
        {
            if(ret_real_play == false)
            {
            	vid_hkocx_obj.LogoutDevice();
            	last_error = -1;
            }
        }
        if(last_error != 0)
        {
            try
            {
                if(video_brand == 200)
                {
                    alert(gettext("预览失败，请确认后重试！原因：")+gettext("HIKVISION_ERROR_"+last_error));
                }
                else if(video_brand == 101)
                {
                    alert(gettext("预览失败，请确认后重试！原因：")+gettext("ZKiVison_ERROR_"+last_error));
                }
                else if(video_brand == 300)
                {
                    alert(gettext("预览失败，请确认后重试！原因：")+gettext("DaHua_ERROR_"+last_error));
                }
            }
            catch(e)
            {
                alert(gettext("预览失败，请确认后重试！错误码：")+last_error);
            }
        }
        return false;
    }
    return true;
}

//视频回放
function vid_playback_bytime(vid_hkocx_obj, vid_brand, vid_channel, start_time, end_time)
{
	var ret = null;
	if(vid_brand == 200)
	{
	    //暂时按照时间来查询，后续可以按照点来查询。"2012-2-26 15:05:00"
	    var info = vid_hkocx_obj.SearchRecordFile(vid_channel, start_time, end_time, 0, 0, "");//查询时间段内的录象文件
	    if(info == "")
	    {
	        var iErrorValue = vid_hkocx_obj.GetError();
	        if(iErrorValue == 7)
	        {
	            alert(gettext("HIKVISION_ERROR_7"));
	        }
	        if(iErrorValue == 4)
	        {
	            alert(gettext("HIKVISION_ERROR_4"));
	        }		
	        if(iErrorValue == 13 || iErrorValue == 2)
	        {
	            alert(gettext("无此权限！"));
	        }
	        return;
	    }
	    if(info == "null")
	    {
	        alert(gettext("没有录像文件！"));
	        return;
	    }
	    ret = vid_hkocx_obj.SetPlayBackTime(start_time, end_time);	//设置回放的起始时间和结束时间 
	    //var ret = vid_hkocx_obj.PlayBackByTime(vid_channel, start_time, end_time);//record_time
	    //alert(ret);
	}
	else if(vid_brand == 300)
	{
		ret = vid_hkocx_obj.ShowPlayback();
	}
    if(!ret)
    {
        $("#id_window_container").hide();
		if(vid_brand == 200)
		{
			var last_error = vid_hkocx_obj.GetLastError();
	        if(last_error != 0)
	        {
	            try
	            {
	                alert(gettext("视频回放失败，请确认后重试！原因：")+gettext("HIKVISION_ERROR_"+last_error));
	            }
	            catch(e)
	            {
	                alert(gettext("视频回放失败，请确认后重试！错误码：")+last_error);
	            }
	        }
	        vid_hkocx_obj.Logout();
	        //vid_hkocx_obj.ClearOCX();控件不支持该函数
		}
		else if(vid_brand == 300)
		{
			vid_hkocx_obj.LogoutDevice();
        	vid_hkocx_obj.CloseLocalPlay();
        	alert(gettext("视频回放失败，请确认后重试！错误码：")+ret);
		}
    }
    else
    {
        $("#id_vid_loading").hide();
        $("#id_window_container").show();
    }
    
    return ret;//true or false 
}
