
$(function(){
	var td=new Date()

	render_widgets($("#id_calculateform"));
	
	$("#id_cometime").val(td.getFullYear()+"-"+N2((td.getMonth()+1))+"-01")
	$("#id_endtime").val(td.getFullYear()+"-"+N2((td.getMonth()+1))+"-"+N2(td.getDate()))
	$.ajax({
	    url:"../../att/choice_widget_for_select_emp/?multiple=T",
	    type:"POST",
	    dataType:"html",
	    success:function(sdata){
	        $("#show_emp_tree").html(sdata);
        }
    });
	
	$('#calculatetabs').tabs("#calculatetabs > div");
	
	

	//统计
	$("#id_calculate").click(function(){
		var st=new Date($("#id_cometime").val().replace(/-/g,"/"));
		var et=new Date($("#id_endtime").val().replace(/-/g,"/"));
		if(st>et)
		{
			alert(gettext("开始日期不能大于结束日期"));
			return;
		}
		if(et>new Date())
		{
			alert(gettext("结束日期不能大于今天"));
			return;
		}
		if(((et-st)>31*24*60*60*1000)|| (et.getMonth()>st.getMonth() && et.getDate()>=st.getDate()))
		{
			alert(gettext("统计只能当月日期，或者天数不能超过开始日期的月份天数！ "));
			return;			
		}
		
		if(!setPostData())
			return ;
		if( confirm(gettext("统统计的时间可能会较长，请耐心等待"))==false)
		{
			return ;
		}
		
		var option={
			url:"../../att/AttReCalc/",			
			type:"POST",
			success:function(data){
				//var tmp=data.split(";")				
				//if( tmp.length>1)
				//	$("#id_ReturnMsg").html("<p>"+tmp[1].substr(8)+"</p>");	
				//alert("OK");
				var typevalue=	parseInt($("#id_current_report").val());
						//$("#caltabs-"+typevalue).click();
						//return;\
						where=""
						//alert(typevalue);
						switch(typevalue)
						{
							case 1:
								where+=""
								posReimburese(where)
								break;
							case 2:
								posCarCost(where)
							
								break;
							case 3:
								CarBalanceReport(where)
								break;
							case 4:
								posLostCar(where)
								break;
							case 5:
								PosTotalReport(where)
								break;
				            case 6:
				            	OrignalRecord(where)
				            	break;
				            case 7:
				            	CheckForget(where)
				            	break;
							case 8:
								LeaveReport(where)
								break;
							case 9:
								PunchCardReport(where)
							default:
								break;
						};
//						$("#id_slide").click();
				
			}
		}
		$("#id_calculateform").ajaxSubmit(option);
	});
	//查询
	$("#id_query").click(function(){
		//alert("ok");
		var where=""
		var typevalue=	parseInt($("#id_current_report").val());
		//$("#caltabs-"+typevalue).click();
		//return;
		switch(typevalue)
		{
			case 1:
				where+=""
				posReimburese(where)
				break;
			case 2:
				posCarCost(where)
			
				break;
			case 3:
				CarBalanceReport(where)
				break;
			case 4:
				posLostCar(where)
				break;
			case 5:
				PosTotalReport(where)
				break;
            case 6:
            	OrignalRecord(where)
            	break;
            case 7:
            	CheckForget(where)
            	break;
			case 8:
				LeaveReport(where)
				break;
			case 9:
				PunchCardReport(where)
			default:
				break;
		};
	});
	//默认显示第一个报表
	//posReimburese("");
});

function getquerystringforid()//退款，卡成本
{
	var where=[]
		ds=[]
	$("#show_emp_tree").find("input[name='deptIDs']").each(function(){
		ds.push($(this).val());
	})
	var depts=ds.toString();
	var users=$("#show_emp_tree").find("div[id^='emp_select_']").get(0).g.get_store_emp();
	$("input[name='UserIDs']").val(users.toString());
	if(users.length==0)
	{
		$("input[name='DeptIDs']").val(depts);
		$("input[name='UserIDs']").val("");
		if(depts.length>0)
		{
			where.push('userid__DeptID__in='+depts)
		}		
	}
	else
	{
		$("input[name='DeptIDs']").val("");
		$("input[name='UserIDs']").val(users.toString());
		if(users.length>0)
		{
			where.push('userid__in='+users)		
		}
	}
	st=$("#id_cometime").val();
	et=$("#id_endtime").val();
	det=new Date(et.replace(/-/g,"/"))
	det.setDate(det.getDate()+1)
	ett=det.getFullYear()+"-"+N2(det.getMonth()+1)+"-"+N2(det.getDate())
	switch(parseInt($("#id_current_report").val()))
	{
		case 1:
			where.push('typeid=4&time__range=("'+ st +'","'+ ett +'")')
			break;
		case 2:
			where.push('typeid=1&time__range=("'+ st +'","'+ ett +'")')
			break;
	}
	return where
}

function getquerystring()
{
	var where=[]
		ds=[]
	$("#show_emp_tree").find("input[name='deptIDs']").each(function(){
		ds.push($(this).val());
	})
	var depts=ds.toString();
	var users=$("#show_emp_tree").find("div[id^='emp_select_']").get(0).g.get_store_emp();
	$("input[name='UserIDs']").val(users.toString());
	if(users.length==0)
	{
		$("input[name='DeptIDs']").val(depts);
		$("input[name='UserIDs']").val("");
		if(depts.length>0)
		{
			where.push('UserID__DeptID__in='+depts)
		}		
	}
	else
	{
		$("input[name='DeptIDs']").val("");
		$("input[name='UserIDs']").val(users.toString());
		if(users.length>0)
		{
			where.push('UserID__in='+users)
		}
	}
	st=$("#id_cometime").val();
	et=$("#id_endtime").val();
	det=new Date(et.replace(/-/g,"/"))
	det.setDate(det.getDate()+1)
	ett=det.getFullYear()+"-"+N2(det.getMonth()+1)+"-"+N2(det.getDate())
	switch(parseInt($("#id_current_report").val()))
	{
		case 3:
			where.push('issuedate__range=("'+ st +'","'+ et +'")')
			break;
		case 4:
			where.push('issuedate__range=("'+ st +'","'+ et +'")')
			break;
		default:
			break;
	}
	return where
}


function setPostData()
{
	ds=[]
	$("#show_emp_tree").find("input[name='deptIDs']").each(function(){
		ds.push($(this).val());
	})
	var depts=ds.toString();		
	var users=$("#show_emp_tree").find("div[id^='emp_select_']").get(0).g.get_store_emp();
	if(depts=="" && users=="")
	{	
		alert(gettext("请选择人员或部门"));
		return false
	}
	$("input[name='UserIDs']").val(users.toString());
	if(users.length==0)
	{
		$("input[name='DeptIDs']").val(depts);
		$("input[name='UserIDs']").val("");
	}
	else
	{
		$("input[name='DeptIDs']").val("");
		$("input[name='UserIDs']").val(users.toString());
	}
	return true
}
//设置报表，操作相关的共用属性
function SetProperty(reportid,app,model,reportname)
{
		//每次点击不同报表时，将清除已经选择的人员列表
		if($("#id_current_report").val()!=reportid);
		{
			
			$("#id_current_report").val(reportid);
			$("#subtabs-"+reportid).empty();
		}
		if(reportid==2 || reportid==5 || reportid==8 || reportid==9)//数据计算模型		
		{
			$("#id_sys_isModelExport").val("false")
		}
		else//数据表模型
		{
			$("#id_sys_isModelExport").val("true")

		}
		if(reportid==2 || reportid==3 || reportid==5 || reportid==8)
		{
			$("#id_attexcept_desc").show();
		}
		else
		{
			$("#id_attexcept_desc").hide();
		}
		$("#id_sys_cur_app").val(app);
   		$("#id_sys_cur_model").val(model);
   		$("#id_sys_cur_grid").val("#subtabs-"+reportid);
   		$("#id_sys_cur_exporttitle").val(reportname);
		
}



function posReimburese(where)//退款明细
{
	SetProperty("1",'pos','CarCashSZ',gettext('退款明细'));
	$("#subtabs-1").model_grid(getPubOpt('pos','CarCashSZ',getquerystringforid()));
}

function posCarCost(where)//卡成本
{
	SetProperty("2",'pos','CarCashSZ',gettext('卡成本'));
	$("#subtabs-2").model_grid(getPubOpt('pos','CarCashSZ',getquerystringforid()));
}

function PosTotalReport(where)
{
	if(!setPostData())
			return ;
	$("#id_calculateform").find("input[name='pa']").remove();	
	var url="../../pos/totalreport/"
	var option={
				url:url,	
				dataType:"json",	
				data:"pa=T",	
				type:"POST",
				success:function(data){
					SetProperty("5",'list',data.tmp_name,gettext('统计最早于最晚'));
					$("#subtabs-5").grid(getDataOpt(data,url));
					
				}
			}
	$("#id_calculateform").ajaxSubmit(option);
	load_description();
	
}



function load_description()
{
	$.ajax({
					url:"../../att/getallexcept/",
					dataType:"json",
					type:"POST",
					success:function(ret){
						var html=""
						data=ret.data
						for(var i=0;i<data.length;i++)
						{
							var tmp=data[i]
							html+="<span>"+tmp[0]+":<span class='color_orange'>"+ tmp[2] +"( "+tmp[1]+" )</span></span>&nbsp;&nbsp;";
						}
						$("#id_attexcept_desc").html(html);
					}
				});
	
}


function CarBalanceReport(where)//卡余额
{
	SetProperty("3",'personnel','IssueCard',gettext('卡余额'));
	$("#subtabs-3").model_grid(getPubOpt('personnel','IssueCard',getquerystring()));
//	if(!setPostData())
//		return ;
//	$("#id_calculateform").find("input[name='pa']").remove();	
//	var url="../../data/personnel/IssueCard/"
//	var option={
//				url:url,	
//				dataType:"json",	
//				data:"pa=T",	
//				type:"POST",
//				success:function(data){
//					SetProperty("3",'list',data.tmp_name,gettext('卡余额'));
//					//$("#subtabs-5").grid(getDataOpt(data,url));
//					$('#subtabs-3').model_grid(
//					        {
//					        'model_url':url,
//					        'model_actions':false,
//					        'object_actions':false,
//					        'obj_edit':false,
//					        'multiple_select':null,
//					        row_operations:false,
//					        fields_show:["UserID.PIN","UserID.EName","UserID.DeptID","code","deptname","cardno","cardstatus","issuedate"],
//					        //disable_cols:["issuedate","Title",'Tele','Mobile','photo','id',"|thumbnail_url:'pin'|photo",'level_count']
//					        },getquerystring())
//					
//				}
//			}
//	$("#id_calculateform").ajaxSubmit(option);
//	load_description();
}	


function posLostCar(where)//卡挂失
{
	SetProperty("4",'personnel','IssueCard',gettext('卡挂失'));
	$("#subtabs-4").model_grid(getPubOpt_lost('personnel','IssueCard',getquerystring()));
}	

getdata=function(opt){
	$.ajax({ 
	   type: "POST",
	   url:opt.url+"?r="+Math.random(),
	   data:opt.data,
	   dataType:"json",
	   success:function(json){
			var gridd=$(opt.ddiv);
			json.multiple_select=null;
			json.on_pager=function(grid,p){
				$.ajax({
					type:"POST",
					url:opt.url+"?p="+p,
					data:opt.data,
					dataType:"json",
					success:function(msg){
						$.extend(grid.g,msg);
						grid.g.reload_data(msg);
					}
				});
			 return false;
			 }; 
			SetProperty("9","list" ,json.tmp_name)
			gridd.grid(json);
			
			
	   }
  })
}

function PunchCardReport(where)
{
	var dt1=$("#id_cometime").val()
	var dt2=$("#id_endtime").val()
	if (dt1=="" || dt2==""){
		alert(gettext("请选择开始日期或结束日期!"));
		return
	}
	if (dt1>dt2){
		alert(gettext("开始日期不能大于结束日期!"));
		return
	}
	var ddt1 = new Date(dt1)
	var ddt2 = new Date(dt2)
    iDays = parseInt(Math.abs(ddt2 - ddt1) / 1000 / 60 / 60 /24) +1
    if (iDays>31){
		alert(gettext("最多只能查询31天的数据!"));
		return
	}
	var depts=$("#show_emp_tree").find("input[name='id_input_department']").val();		
	var users=$("#show_emp_tree").find("div[id^='emp_select_']").get(0).g.get_store_emp();
	
	postdata={"starttime":dt1,"endtime":dt2,"deptids":depts,"empids":users}
	getdata({"url":"../../att/GenerateEmpPunchCard/","ddiv":"#subtabs-9","data":postdata})
	
	
}
	
function getUserId(g)
{
	
	var rid=$("#id_current_report").val();
	var userids=[]
	if(g==undefined)
		return userids
	if(rid==2 || rid==5 ||rid==8 )
	{
		var selected=g.get_selected().indexes
		for(var s=0	;s< selected.length;s++)
		{
			var tmp=g.data[selected[s]][0]			
			userids.push(tmp)
		}		
	}
	else
	{
		var selected=g.get_selected().indexes
		for(var s=0	;s< selected.length;s++)
		{
			var tmp=g.data[selected[s]][1]
//			tmp=tmp.substr(0,tmp.indexOf(" "));
			userids.push(tmp)
		}
	}
	return userids
	
}
function showDialog(url,title,width,height,event)
{
	var advhtml=""
    var userlist=[]
    var sdata={}
	var userid=getUserId($("#calculatetabs").find("#subtabs-"+$("#id_current_report").val()).get(0).g);  //查询结果中选择的人员
	
	if( userid.length<=0)
	{
		alert(gettext('请在查询结果中选择人员！'));
		return;
	}
	//alert(selected.toString());
	//var userid=selected.query_string;
	//userid=userid.replace(/K/g,'UserID');
	var tmp=[]
	for(var i=0;i<userid.length;i++)
	{
		var append=true;
		for(var j=0;j<tmp.length;j++)
		{
			if(tmp[j]==userid[i])
			{
				append=false;
				break;
			}
		}
		if(append)
		{
			tmp.push(userid[i]);
		}
	}
	userid=tmp

	$.ajax({
		type:"GET",
		url:url+"?_lock=1&UserID="+userid.join("&UserID="),
		//async:false,
		success:function(data){
		
			$(data).find("#id_span_title").hide();	
			advhtml=$("<div id='id_list'>"+data+"<div id='id_result_error'></div></div>")

			
			var cancel=function(div){					
				$("#id_list").find("#id_close").click();
			};
			var save_ok=function(){	
				if(!advhtml.find("#id_edit_form").valid())
				{
					return;
				}
				
				var opt={
					type:"POST",
					url:url,
					success:function(data){
						
						//alert(data);					
						if(data=='{ Info:"OK" }')
						{
							$("#id_list").find("#id_close").click();
						}else{
							$("#id_result_error").html("").append($(data).find(".errorlist").eq(0));
						}
					}					
				}		
				advhtml.find("#id_edit_form").ajaxSubmit(opt);		
			};
			//alert($(advhtml).find(".form_help").length);
			advhtml.find(".form_help").remove();
			advhtml.find(".zd_Emp").addClass("displayN");
			advhtml.find("#id_span_title").remove();
			advhtml.find("#objs_for_op").addClass("displayN");
			var d={}
			d["buttons"]={}
			d["buttons"][gettext('确认')]=save_ok;
			d["buttons"][gettext('取消')]=cancel;
			d["title"]=title;
			advhtml.dialog(d);	
		}
	});    	
	
	return;
}
function N2(nc)
{
	var tt= "00"  +nc.toString()
   
    tt=tt.toString();
    return tt.substr(tt.length-2);
}   
/*just for test*/
function FlushCard(where)
{
	SetProperty("9",'pos','CarCashSZ',gettext('消费刷卡记录表'));
	//alert(getquerystring());
	where = getquerystring();//+'&typeid='+7
	where.push('typeid=7');
	$("#subtabs-9").model_grid(getPubOpt('pos','CarCashSZ', where));/*消费类型*/
}
function ChargeRecord(where)
{
	SetProperty("8",'pos','CarCashSZ',gettext('充值表'));
	where = getquerystring();//+'&typeid='+7
	where.push('typeid=2');
	$("#subtabs-8").model_grid(getPubOpt('pos','CarCashSZ',where));
}
function IssueCard(where)
{
	SetProperty("7",'pos','CarCashSZ',gettext('发卡表'));
	where = getquerystring();//+'&typeid='+7
	where.push('typeid=1');
	$("#subtabs-7").model_grid(getPubOpt('pos','CarCashSZ',where));
}

function ReturnCard(where)
{
	SetProperty("6",'pos','CarCashSZ',gettext('退卡记录表'));
	where = getquerystring();//+'&typeid='+7
	where.push('typeid=3');
	$("#subtabs-6").model_grid(getPubOpt('pos','CarCashSZ',where));
}

function Allowance(where)
{
	SetProperty("10",'pos','CarCashSZ',gettext('补助表'));
	where = getquerystring();//+'&typeid='+7
	where.push('typeid=5');
	$("#subtabs-10").model_grid(getPubOpt('pos','CarCashSZ',where));
}
function DateCash(where)
{
	SetProperty("11",'pos','CarCashSZ',gettext('日现金流表'));
	$("#subtabs-11").model_grid(getPubOpt('pos','CarCashSZ',getquerystring()));
}
/*end test*/