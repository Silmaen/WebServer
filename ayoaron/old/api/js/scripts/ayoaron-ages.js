/*==================================================
 *  Japanese Era Date Labeller
 *==================================================
 */

Timeline.AyoaronAgeDateLabeller = function(locale) {
	this._local = locale;
	this._timezone = 0;
};

Timeline.AyoaronAgeDateLabeller.labelIntervalFunctions = [];

Timeline.AyoaronAgeDateLabeller.getMonthName = function(amonth) {
	var text = amonth;
	switch(amonth) {
	case 0:
		text ="Mitar";
		break;
	case 1:
		text ="Morer";
		break;
	case 2:
		text ="Mebir";
		break;
	case 3:
		text ="Mujur";
		break;
	case 4:
		text ="Mastur";
		break;
	case 5:
		text ="Ritam";
		break;
	case 6:
		text ="Rorem";
		break;
	case 7:
		text ="Rebim";
		break;
	case 8:
		text ="Rujum";
		break;
	case 9:
		text ="Rastum";
		break;
	case 10:
		text ="Sestir";
		break;
	}
	return text;
};

Timeline.AyoaronAgeDateLabeller.ADatetoStr = function(date) {
	var age    = SimileAjax.DateTime.getUnitDate(date,SimileAjax.DateTime.AGE,"ayoaron");
	var year   = SimileAjax.DateTime.getUnitDate(date,SimileAjax.DateTime.YEAR,"ayoaron");
	var month  = SimileAjax.DateTime.getUnitDate(date,SimileAjax.DateTime.MONTH,"ayoaron");
	var day    = SimileAjax.DateTime.getUnitDate(date,SimileAjax.DateTime.DAY,"ayoaron");
	var heure  = SimileAjax.DateTime.getUnitDate(date,SimileAjax.DateTime.HOUR,"ayoaron");
	var minute = SimileAjax.DateTime.getUnitDate(date,SimileAjax.DateTime.MINUTE,"ayoaron");
	var second = SimileAjax.DateTime.getUnitDate(date,SimileAjax.DateTime.SECOND,"ayoaron");
	var sheure  = (heure >9)? heure : "0"+heure;
	var sminute = (minute>9)? minute: "0"+minute;
	var ssecond = (second>9)? second: "0"+second;
	if (year > 0 ){
		tage="O ";
		if (age == 1) {
			tage = "I ";
		} else if (age == 2 ) {
			tage = "II ";
		} else if (age == 3) {
			tage = "III ";
		} else if (age != 0){
			tage = "IV ";
		}
		var text = tage + year + " " + Timeline.AyoaronAgeDateLabeller.getMonthName(month) + " " + day + " " + sheure + ":" + sminute + ":" + ssecond;
	}else{
		var text = year + " " + Timeline.AyoaronAgeDateLabeller.getMonthName(month) + " " + day + " " + sheure + ":" + sminute + ":" + ssecond;
	}
	return text;
};

Timeline.AyoaronAgeDateLabeller.prototype.labelInterval = function(date, intervalUnit) {
    var f = Timeline.AyoaronAgeDateLabeller.labelIntervalFunctions[this._locale];
    if (f == null) {
        f = Timeline.AyoaronAgeDateLabeller.prototype.defaultLabelInterval;
    }
    return f.call(this, date, intervalUnit);
};

Timeline.AyoaronAgeDateLabeller.prototype.defaultLabelInterval = function(date, intervalUnit) {
	var text;
	var emphasized = false;

	switch(intervalUnit) {
	case SimileAjax.DateTime.MILLISECOND:
		text = SimileAjax.DateTime.getUnitDate(date,intervalUnit,"ayoaron");
		break;
	case SimileAjax.DateTime.SECOND:
		text = SimileAjax.DateTime.getUnitDate(date,intervalUnit,"ayoaron");
		break;
	case SimileAjax.DateTime.MINUTE:
		var m = SimileAjax.DateTime.getUnitDate(date,intervalUnit,"ayoaron");
		if (m == 0) {
			text = SimileAjax.DateTime.getUnitDate(date,SimileAjax.DateTime.HOUR,"ayoaron") + ":00";
			emphasized = true;
		} else {
			text = m;
		}
		break;
	case SimileAjax.DateTime.HOUR:
		text = SimileAjax.DateTime.getUnitDate(date,intervalUnit,"ayoaron") + "hr";
		break;
	case SimileAjax.DateTime.DAY:
	case SimileAjax.DateTime.WEEK:
		//OLD text = Timeline.GregorianDateLabeller.getMonthName(date.getUTCMonth(), this._locale) + " " + date.getUTCDate();
		var day = SimileAjax.DateTime.getUnitDate(date,intervalUnit,"ayoaron");
		if (day == 1 ){
			text = Timeline.AyoaronAgeDateLabeller.getMonthName(SimileAjax.DateTime.getUnitDate(date,SimileAjax.DateTime.MONTH,"ayoaron")) + " " + day;
		}else{
			text = day;
		}
		break;
	case SimileAjax.DateTime.MONTH:
		// OLD var m = date.getUTCMonth();
		var m = SimileAjax.DateTime.getUnitDate(date,intervalUnit,"ayoaron");
		if (m != 0) {
			//OLD text = Timeline.GregorianDateLabeller.getMonthName(m, this._locale);
			text = Timeline.AyoaronAgeDateLabeller.getMonthName(m);
			break;
		} // else, fall through
	case SimileAjax.DateTime.YEAR:
	case SimileAjax.DateTime.DECADE:
	case SimileAjax.DateTime.CENTURY:
	case SimileAjax.DateTime.MILLENNIUM:
		/* OLD var y = date.getUTCFullYear();
		if (y > 0) {
			text = date.getUTCFullYear();
		} else {
			text = (1 - y) + "BC";
		} */
		// je converti en AGE - année 'à la main'
		var age  = SimileAjax.DateTime.getUnitDate(date,SimileAjax.DateTime.AGE ,"ayoaron");
		var year = SimileAjax.DateTime.getUnitDate(date,SimileAjax.DateTime.YEAR,"ayoaron");
		var tage = "";
		if ( year >= 0 ) {
			tage="O ";
			if (age == 1) {
				tage = "I ";
			} else if (age == 2 ) {
				tage = "II ";
			} else if (age == 3) {
				tage = "III ";
			} else if (age != 0){
				tage = "IV ";
			}
		}
		text = tage + (year);
		emphasized = 
			(intervalUnit == SimileAjax.DateTime.MONTH) ||
			(intervalUnit == SimileAjax.DateTime.DECADE && year % 100 == 0) || 
			(intervalUnit == SimileAjax.DateTime.CENTURY && year % 1000 == 0);
		break;
	default:
		text = Timeline.AyoaronAgeDateLabeller.ADatetoStr(date);
	}
	 return { text: text, emphasized: emphasized };
};

Timeline.AyoaronAgeDateLabeller.prototype.labelPrecise = function(date) {
    return Timeline.AyoaronAgeDateLabeller.ADatetoStr(date);
};
