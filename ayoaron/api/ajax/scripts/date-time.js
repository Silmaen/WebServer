/**
 * @fileOverview A collection of date/time utility functions
 * @name SimileAjax.DateTime
 */

SimileAjax.DateTime = new Object();

SimileAjax.DateTime.MILLISECOND    = 0;
SimileAjax.DateTime.SECOND         = 1;
SimileAjax.DateTime.MINUTE         = 2;
SimileAjax.DateTime.HOUR           = 3;
SimileAjax.DateTime.DAY            = 4;
SimileAjax.DateTime.WEEK           = 5;
SimileAjax.DateTime.MONTH          = 6;
SimileAjax.DateTime.YEAR           = 7;
SimileAjax.DateTime.DECADE         = 8;
SimileAjax.DateTime.CENTURY        = 9;
SimileAjax.DateTime.MILLENNIUM     = 10;
SimileAjax.DateTime.AGE            = 11;

SimileAjax.DateTime.EPOCH          = -1;
SimileAjax.DateTime.ERA            = -2;

/**
 * An array of unit lengths, expressed in milliseconds, of various lengths of
 * time.  The array indices are predefined and stored as properties of the
 * SimileAjax.DateTime object, e.g. SimileAjax.DateTime.YEAR.
 * @type Array
 */
SimileAjax.DateTime.gregorianUnitLengths = [];
    (function() {
        var d = SimileAjax.DateTime;
        var a = d.gregorianUnitLengths;
        
        a[d.MILLISECOND] = 1;
        a[d.SECOND]      = 1000;
        a[d.MINUTE]      = a[d.SECOND] * 60;
        a[d.HOUR]        = a[d.MINUTE] * 60;
        a[d.DAY]         = a[d.HOUR] * 24;
        a[d.WEEK]        = a[d.DAY] * 7;
        a[d.MONTH]       = a[d.DAY] * 31;
        a[d.YEAR]        = a[d.DAY] * 365;
        a[d.DECADE]      = a[d.YEAR] * 10;
        a[d.CENTURY]     = a[d.YEAR] * 100;
        a[d.MILLENNIUM]  = a[d.YEAR] * 1000;
    })();
    
SimileAjax.DateTime.ayoaronUnitLengths = [];
    (function() {
        var d = SimileAjax.DateTime;
        var a = d.ayoaronUnitLengths;
        
        a[d.MILLISECOND] = 1;
        a[d.SECOND]      = 1000;
        a[d.MINUTE]      = a[d.SECOND] * 60;
        a[d.HOUR]        = a[d.MINUTE] * 60;
        a[d.DAY]         = a[d.HOUR] * 24;
        a[d.WEEK]        = a[d.DAY] * 7;
        a[d.MONTH]       = a[d.DAY] * 35;
        a[d.YEAR]        = a[d.DAY] * 365;
        a[d.DECADE]      = a[d.YEAR] * 10;
        a[d.CENTURY]     = a[d.YEAR] * 100;
        a[d.MILLENNIUM]  = a[d.YEAR] * 1000;
    })();    

    
SimileAjax.DateTime._dateRegexp = new RegExp(
    "^(-?)([0-9]{4})(" + [
        "(-?([0-9]{2})(-?([0-9]{2}))?)", // -month-dayOfMonth
        "(-?([0-9]{3}))",                // -dayOfYear
        "(-?W([0-9]{2})(-?([1-7]))?)"    // -Wweek-dayOfWeek
    ].join("|") + ")?$"
);
SimileAjax.DateTime._timezoneRegexp = new RegExp(
    "Z|(([-+])([0-9]{2})(:?([0-9]{2}))?)$"
);
SimileAjax.DateTime._timeRegexp = new RegExp(
    "^([0-9]{2})(:?([0-9]{2})(:?([0-9]{2})(\.([0-9]+))?)?)?$"
);

SimileAjax.DateTime.getUnitDate = function(date,unit,system){
	var tSystem = (typeof system == 'undefined') ? "gregorian" : system;
	var tunit   = (typeof unit   == 'undefined') ? 0           : unit;
	var ddate2 = new Date(date.getTime());
	switch(tSystem){
	case "ayoaron":
		var p = SimileAjax.DateTime;
		var offset = 9913 * p.ayoaronUnitLengths[p.YEAR];
		var milis = date.getTime() + offset;
		
		switch(tunit){
		case p.MILLISECOND:
			var mmin = Math.floor((milis)     /p.ayoaronUnitLengths[p.SECOND])*p.ayoaronUnitLengths[p.SECOND];
			return    (Math.floor((milis-mmin)/p.ayoaronUnitLengths[p.MILLISECOND]));
			break;
		case p.SECOND:
			var mmin = Math.floor((milis)     /p.ayoaronUnitLengths[p.MINUTE])*p.ayoaronUnitLengths[p.MINUTE];
			return    (Math.floor((milis-mmin)/p.ayoaronUnitLengths[p.SECOND]));
			break;
		case p.MINUTE:
			var mhou = Math.floor((milis)     /p.ayoaronUnitLengths[p.HOUR])*p.ayoaronUnitLengths[p.HOUR];
			return    (Math.floor((milis-mhou)/p.ayoaronUnitLengths[p.MINUTE]));
			break;
		case p.HOUR:
			var mday = Math.floor((milis)     /p.ayoaronUnitLengths[p.DAY])*p.ayoaronUnitLengths[p.DAY];
			return    (Math.floor((milis-mday)/p.ayoaronUnitLengths[p.HOUR]));
			break;
		case p.DAY:
			var myear = Math.floor( milis           /p.ayoaronUnitLengths[p.YEAR] )*p.ayoaronUnitLengths[p.YEAR];
			var mon   = Math.floor((milis-myear)    /p.ayoaronUnitLengths[p.MONTH])*p.ayoaronUnitLengths[p.MONTH];
			return     (Math.floor((milis-myear-mon)/p.ayoaronUnitLengths[p.DAY]  ) + 1);
			break;
		case p.MONTH:
			var myear = Math.floor( milis       /p.ayoaronUnitLengths[p.YEAR])*p.ayoaronUnitLengths[p.YEAR];
			return      Math.floor((milis-myear)/p.ayoaronUnitLengths[p.MONTH]);
			break;
		case p.YEAR:
			var year = Math.floor(milis/p.ayoaronUnitLengths[p.YEAR]);
			if (year < 1756) {
				return year;
			} else if (year < 5345) {
				return year - 1756;
			} else if (year < 8459) {
				return year - 5345;
			} else if (year < 9948) {
				return year - 8459;
			} else {
				return year - 9948;
			}
			break;
		case p.DECADE:
			var year = Math.floor(milis/p.ayoaronUnitLengths[p.YEAR]);
			if (year < 5345) {
				year -= 1756;
			} else if (year < 8459) {
				year -= 5345;
			} else if (year < 9948) {
				year -= 8459;
			} else {
				year -= 9948;
			}
			return Math.floor(year/10);
			break;
		case p.CENTURY:
			var year = Math.floor(milis/p.ayoaronUnitLengths[p.YEAR]);
			if (year < 5345) {
				year -= 1756;
			} else if (year < 8459) {
				year -= 5345;
			} else if (year < 9948) {
				year -= 8459;
			} else {
				year -= 9948;
			}
			return Math.floor(year/100);
			break;
		case p.MILLENNIUM:
			var year = Math.floor(milis/p.ayoaronUnitLengths[p.YEAR]);
			if (year < 5345) {
				year -= 1756;
			} else if (year < 8459) {
				year -= 5345;
			} else if (year < 9948) {
				year -= 8459;
			} else {
				year -= 9948;
			}
			return Math.floor(year/1000);
			break;
		case p.AGE:
			var year = Math.floor(milis/p.ayoaronUnitLengths[p.YEAR]);
			if (year < 1756) {
				return 0;
			} else if (year < 5345) {
				return 1;
			} else if (year < 8459) {
				return 2;
			} else if (year < 9948) {
				return 3;
			} else {
				return 4;
			}
			break;
		}
		break;
	case "gregorian":
	default:
		alert("get gregorian");
		switch(tunit){
		case SimileAjax.DateTime.MILLISECOND:
			return date.getUTCMilliseconds();
			break;
		case SimileAjax.DateTime.SECOND:
			return date.getUTCSeconds();
			break;
		case SimileAjax.DateTime.MINUTE:
			return date.getUTCMinutes();
			break;
		case SimileAjax.DateTime.HOUR:
			return date.getUTCHours();
			break;
		case SimileAjax.DateTime.DAY:
			return date.getUTCDate();
			break;
		case SimileAjax.DateTime.WEEK:
			break;
		case SimileAjax.DateTime.MONTH:
			return date.getUTCMonth();
			break;
		case SimileAjax.DateTime.YEAR:
		case SimileAjax.DateTime.AGE:
			return date.getUTCFullYear();
			break;
		case SimileAjax.DateTime.DECADE:
			return Math.floor(date.getUTCFullYear()/10);
			break;
		case SimileAjax.DateTime.CENTURY:
			return Math.floor(date.getUTCFullYear()/100);
			break;
		case SimileAjax.DateTime.MILLENNIUM:
			return Math.floor(date.getUTCFullYear()/1000);
			break;
		}
	}
}

SimileAjax.DateTime.setUnitDate = function(date,val,unit,system){
	var tSystem = (typeof system == 'undefined') ? "gregorian" : system;
	var tunit   = (typeof unit   == 'undefined') ? 0           : unit;
	switch(tSystem){
	case "ayoaron":
		var p = SimileAjax.DateTime;
		var age = p.getUnitDate(date,unit,system);
		var offset = 9913 * p.ayoaronUnitLengths[p.YEAR];
		var milis = date.getTime() + offset;
		switch(tunit){
		case p.MILLISECOND:
		case p.SECOND:
		case p.MINUTE:
		case p.HOUR:
		case p.DAY:
		case p.MONTH:
		case p.YEAR:
		case p.DECADE:
		case p.CENTURY:
		case p.MILLENNIUM:
			date.setTime(milis+(val-age)*p.ayoaronUnitLengths[unit]-offset);
			break;
		case SimileAjax.DateTime.AGE:
			var dyear = 0;
			if ( age == 1 ) dyear = 1756;
			if ( age == 2 ) dyear = 5345;
			if ( age == 3 ) dyear = 8459;
			if ( age >= 4 ) dyear = 9948;
			var ayear = 0;
			if ( val == 1 ) ayear = 1756;
			if ( val == 2 ) ayear = 5345;
			if ( val == 3 ) ayear = 8459;
			if ( val >= 4 ) ayear = 9948;
			date.setTime(milis+(ayear-dyear)*p.ayoaronUnitLengths[p.YEAR]-offset);
			break;
		}
		break;
	case "gregorian":
	default:
		//alert("set date gregorian");
		switch(tunit){
		case SimileAjax.DateTime.MILLISECOND:
			date.setUTCMilliseconds(val);
			break;
		case SimileAjax.DateTime.SECOND:
			date.setUTCSeconds(val);
			break;
		case SimileAjax.DateTime.MINUTE:
			date.setUTCMinutes(val);
			break;
		case SimileAjax.DateTime.HOUR:
			date.setUTCHours(val);
			break;
		case SimileAjax.DateTime.DAY:
			date.setUTCDate(val+1);
			break;
		case SimileAjax.DateTime.WEEK:
			break;
		case SimileAjax.DateTime.MONTH:
			date.setUTCMonth(val);
			break;
		case SimileAjax.DateTime.YEAR:
		case SimileAjax.DateTime.AGE:
			date.setUTCFullYear(val);
			break;
		case SimileAjax.DateTime.DECADE:
			date.setUTCFullYear(val*10);
			break;
		case SimileAjax.DateTime.CENTURY:
			date.setUTCFullYear(val*100);
			break;
		case SimileAjax.DateTime.MILLENNIUM:
			date.setUTCFullYear(val*1000);
			break;
		}
	}
}


/**
 * Takes a date object and a string containing an ISO 8601 date and sets the
 * the date using information parsed from the string.  Note that this method
 * does not parse any time information.
 *
 * @param {Date} dateObject the date object to modify
 * @param {String} string an ISO 8601 string to parse
 * @return {Date} the modified date object
 */
SimileAjax.DateTime.setIso8601Date = function(dateObject, string) {
    /*
     *  This function has been adapted from dojo.date, v.0.3.0
     *  http://dojotoolkit.org/.
     */
     
    var d = string.match(SimileAjax.DateTime._dateRegexp);
    if(!d) {
        throw new Error("Invalid date string: " + string);
    }
    
    var sign = (d[1] == "-") ? -1 : 1; // BC or AD
    var year = sign * d[2];
    var month = d[5];
    var date = d[7];
    var dayofyear = d[9];
    var week = d[11];
    var dayofweek = (d[13]) ? d[13] : 1;

    dateObject.setUTCFullYear(year);
    if (dayofyear) { 
        dateObject.setUTCMonth(0);
        dateObject.setUTCDate(Number(dayofyear));
    } else if (week) {
        dateObject.setUTCMonth(0);
        dateObject.setUTCDate(1);
        var gd = dateObject.getUTCDay();
        var day =  (gd) ? gd : 7;
        var offset = Number(dayofweek) + (7 * Number(week));
        
        if (day <= 4) { 
            dateObject.setUTCDate(offset + 1 - day); 
        } else { 
            dateObject.setUTCDate(offset + 8 - day); 
        }
    } else {
        if (month) { 
            dateObject.setUTCDate(1);
            dateObject.setUTCMonth(month - 1); 
        }
        if (date) { 
            dateObject.setUTCDate(date); 
        }
    }
    
    return dateObject;
};

/**
 * Takes a date object and a string containing an ISO 8601 time and sets the
 * the time using information parsed from the string.  Note that this method
 * does not parse any date information.
 *
 * @param {Date} dateObject the date object to modify
 * @param {String} string an ISO 8601 string to parse
 * @return {Date} the modified date object
 */
SimileAjax.DateTime.setIso8601Time = function (dateObject, string) {
    /*
     *  This function has been adapted from dojo.date, v.0.3.0
     *  http://dojotoolkit.org/.
     */
    
    var d = string.match(SimileAjax.DateTime._timeRegexp);
    if(!d) {
        SimileAjax.Debug.warn("Invalid time string: " + string);
        return false;
    }
    var hours = d[1];
    var mins = Number((d[3]) ? d[3] : 0);
    var secs = (d[5]) ? d[5] : 0;
    var ms = d[7] ? (Number("0." + d[7]) * 1000) : 0;

    dateObject.setUTCHours(hours);
    dateObject.setUTCMinutes(mins);
    dateObject.setUTCSeconds(secs);
    dateObject.setUTCMilliseconds(ms);
    
    return dateObject;
};

/**
 * The timezone offset in minutes in the user's browser.
 * @type Number
 */
SimileAjax.DateTime.timezoneOffset = new Date().getTimezoneOffset();

/**
 * Takes a date object and a string containing an ISO 8601 date and time and 
 * sets the date object using information parsed from the string.
 *
 * @param {Date} dateObject the date object to modify
 * @param {String} string an ISO 8601 string to parse
 * @return {Date} the modified date object
 */
SimileAjax.DateTime.setIso8601 = function (dateObject, string){
    /*
     *  This function has been adapted from dojo.date, v.0.3.0
     *  http://dojotoolkit.org/.
     */
     
    var offset = null;
    var comps = (string.indexOf("T") == -1) ? string.split(" ") : string.split("T");
    
    SimileAjax.DateTime.setIso8601Date(dateObject, comps[0]);
    if (comps.length == 2) { 
        // first strip timezone info from the end
        var d = comps[1].match(SimileAjax.DateTime._timezoneRegexp);
        if (d) {
            if (d[0] == 'Z') {
                offset = 0;
            } else {
                offset = (Number(d[3]) * 60) + Number(d[5]);
                offset *= ((d[2] == '-') ? 1 : -1);
            }
            comps[1] = comps[1].substr(0, comps[1].length - d[0].length);
        }

        SimileAjax.DateTime.setIso8601Time(dateObject, comps[1]); 
    }
    if (offset == null) {
        offset = dateObject.getTimezoneOffset(); // local time zone if no tz info
    }
    dateObject.setTime(dateObject.getTime() + offset * 60000);
    
    return dateObject;
};

/**
 * Takes a string containing an ISO 8601 date and returns a newly instantiated
 * date object with the parsed date and time information from the string.
 *
 * @param {String} string an ISO 8601 string to parse
 * @return {Date} a new date object created from the string
 */
SimileAjax.DateTime.parseIso8601DateTime = function (string) {
    try {
        return SimileAjax.DateTime.setIso8601(new Date(0), string);
    } catch (e) {
        return null;
    }
};

SimileAjax.DateTime.parseAyoaronDateTime = function(o) {
	if (o == null) {
		return null;
	} else if (o instanceof Date) {
		return o;
	}
	var age = 0;
	var year = 0;
	var mon = 0;
	var day = 0;
	var hour = 0;
	var minu = 0;
	var seco = 0;
	//o est une string...
	var stdate = o.split(" ");
	//traitement de l'age
	if (stdate[0] == "I" ) age=1;
	if (stdate[0] == "II" ) age=2;
	if (stdate[0] == "III" ) age=3;
	if (stdate[0] == "IV" ) age=4;
	//traitement annee mois jour
	var amjdate = stdate[1].split("-");
	year=parseInt(amjdate[0]);
	mon=parseInt(amjdate[1]);
	day=parseInt(amjdate[2]);
	//traitement heur minute seconde
	var hmsdate = stdate[2].split(":");
	hour=parseInt(hmsdate[0]);
	minu=parseInt(hmsdate[1]);
	seco=parseInt(hmsdate[2]);
	//--------------------
	var date = new Date(0);
	SimileAjax.DateTime.setUnitDate(date,age ,SimileAjax.DateTime.AGE   ,"ayoaron");
	SimileAjax.DateTime.setUnitDate(date,year,SimileAjax.DateTime.YEAR  ,"ayoaron");
	SimileAjax.DateTime.setUnitDate(date,mon ,SimileAjax.DateTime.MONTH ,"ayoaron");
	SimileAjax.DateTime.setUnitDate(date,day ,SimileAjax.DateTime.DAY   ,"ayoaron");
	SimileAjax.DateTime.setUnitDate(date,hour,SimileAjax.DateTime.HOUR  ,"ayoaron");
	SimileAjax.DateTime.setUnitDate(date,minu,SimileAjax.DateTime.MINUTE,"ayoaron");
	SimileAjax.DateTime.setUnitDate(date,seco,SimileAjax.DateTime.SECOND,"ayoaron");
	
	
	/*var age2  = SimileAjax.DateTime.getUnitDate(date,SimileAjax.DateTime.AGE   ,"ayoaron");
	var year2 = SimileAjax.DateTime.getUnitDate(date,SimileAjax.DateTime.YEAR  ,"ayoaron");
	var mon2  = SimileAjax.DateTime.getUnitDate(date,SimileAjax.DateTime.MONTH ,"ayoaron");
	var day2  = SimileAjax.DateTime.getUnitDate(date,SimileAjax.DateTime.DAY   ,"ayoaron");
	var hour2 = SimileAjax.DateTime.getUnitDate(date,SimileAjax.DateTime.HOUR  ,"ayoaron");
	var minu2 = SimileAjax.DateTime.getUnitDate(date,SimileAjax.DateTime.MINUTE,"ayoaron");
	var seco2 = SimileAjax.DateTime.getUnitDate(date,SimileAjax.DateTime.SECOND,"ayoaron");
	alert("date lue: \n"+
			age+" "+year+"-"+mon+"-"+day+" "+hour+":"+minu+":"+seco+
			"\ndate ecrite: \n"+
			age2+" "+year2+"-"+mon2+"-"+day2+" "+hour2+":"+minu2+":"+seco2);*/
	
	return date;
}

/**
 * Takes a string containing a Gregorian date and time and returns a newly
 * instantiated date object with the parsed date and time information from the
 * string.  If the param is actually an instance of Date instead of a string, 
 * simply returns the given date instead.
 *
 * @param {Object} o an object, to either return or parse as a string
 * @return {Date} the date object
 */
SimileAjax.DateTime.parseGregorianDateTime = function(o) {
    if (o == null) {
        return null;
    } else if (o instanceof Date) {
        return o;
    }
    
    var s = o.toString();
    if (s.length > 0 && s.length < 8) {
        var space = s.indexOf(" ");
        if (space > 0) {
            var year = parseInt(s.substr(0, space));
            var suffix = s.substr(space + 1);
            if (suffix.toLowerCase() == "bc") {
                year = 1 - year;
            }
        } else {
            var year = parseInt(s);
        }
            
        var d = new Date(0);
        d.setUTCFullYear(year);
        
        return d;
    }
    
    try {
        return new Date(Date.parse(s));
    } catch (e) {
        return null;
    }
};

/**
 * Rounds date objects down to the nearest interval or multiple of an interval.
 * This method modifies the given date object, converting it to the given
 * timezone if specified.
 * 
 * @param {Date} date the date object to round
 * @param {Number} intervalUnit a constant, integer index specifying an 
 *   interval, e.g. SimileAjax.DateTime.HOUR
 * @param {Number} timeZone a timezone shift, given in hours
 * @param {Number} multiple a multiple of the interval to round by
 * @param {Number} firstDayOfWeek an integer specifying the first day of the
 *   week, 0 corresponds to Sunday, 1 to Monday, etc.
 */
SimileAjax.DateTime.roundDownToInterval = function(date, intervalUnit, timeZone, multiple, firstDayOfWeek, system) {
	var tSystem = (typeof system == 'undefined') ? "gregorian" : system;
	var timeShift = timeZone * 
		SimileAjax.DateTime.gregorianUnitLengths[SimileAjax.DateTime.HOUR];

	var date2 = new Date(date.getTime() + timeShift);
	var clearInDay = function(d) {
		SimileAjax.DateTime.setUnitDate(d,0,SimileAjax.DateTime.MILLISECOND,tSystem);
		SimileAjax.DateTime.setUnitDate(d,0,SimileAjax.DateTime.SECOND     ,tSystem);
		SimileAjax.DateTime.setUnitDate(d,0,SimileAjax.DateTime.MINUTE     ,tSystem);
		SimileAjax.DateTime.setUnitDate(d,0,SimileAjax.DateTime.HOUR       ,tSystem);
	};
	var clearInYear = function(d) {
		clearInDay(d);
		SimileAjax.DateTime.setUnitDate(d,0,SimileAjax.DateTime.DAY  ,tSystem);
		SimileAjax.DateTime.setUnitDate(d,0,SimileAjax.DateTime.MONTH,tSystem);
	};

	switch(intervalUnit) {
	case SimileAjax.DateTime.SECOND:
		SimileAjax.DateTime.setUnitDate(d,0,SimileAjax.DateTime.MILLISECOND,tSystem);
		break;
	case SimileAjax.DateTime.MINUTE:
		SimileAjax.DateTime.setUnitDate(d,0,SimileAjax.DateTime.MILLISECOND,tSystem);
		SimileAjax.DateTime.setUnitDate(d,0,SimileAjax.DateTime.SECOND     ,tSystem);
		break;
	case SimileAjax.DateTime.HOUR:
		SimileAjax.DateTime.setUnitDate(d,0,SimileAjax.DateTime.MILLISECOND,tSystem);
		SimileAjax.DateTime.setUnitDate(d,0,SimileAjax.DateTime.SECOND     ,tSystem);
		SimileAjax.DateTime.setUnitDate(d,0,SimileAjax.DateTime.MINUTE     ,tSystem);
		break;
	case SimileAjax.DateTime.DAY:
		clearInDay(date2);
		break;
	case SimileAjax.DateTime.WEEK:
		clearInDay(date2);
		var d = (date2.getUTCDay() + 7 - firstDayOfWeek) % 7;
		date2.setTime(date2.getTime() - 
				d * SimileAjax.DateTime.gregorianUnitLengths[SimileAjax.DateTime.DAY]);
		break;
	case SimileAjax.DateTime.MONTH:
		clearInDay(date2);
		SimileAjax.DateTime.setUnitDate(d,0,SimileAjax.DateTime.DAY  ,tSystem);
		break;
	case SimileAjax.DateTime.YEAR:
		clearInYear(date2);
		break;
	case SimileAjax.DateTime.DECADE:
		clearInYear(date2);
		var x = Math.floor(SimileAjax.DateTime.getUnitDate(date2,SimileAjax.DateTime.YEAR,tSystem)/10)*10;
		SimileAjax.DateTime.setUnitDate(date2, x ,SimileAjax.DateTime.YEAR,tSystem);
		break;
	case SimileAjax.DateTime.CENTURY:
		clearInYear(date2);
		var x = Math.floor(SimileAjax.DateTime.getUnitDate(date2,SimileAjax.DateTime.YEAR,tSystem)/100)*100;
		SimileAjax.DateTime.setUnitDate(date2, x ,SimileAjax.DateTime.YEAR,tSystem);
		break;
	case SimileAjax.DateTime.MILLENNIUM:
		clearInYear(date2);
		var x = Math.floor(SimileAjax.DateTime.getUnitDate(date2,SimileAjax.DateTime.YEAR,tSystem)/1000)*1000;
		SimileAjax.DateTime.setUnitDate(date2, x ,SimileAjax.DateTime.YEAR,tSystem);
		break;
	}

	date.setTime(date2.getTime() - timeShift);
};

/**
 * Rounds date objects up to the nearest interval or multiple of an interval.
 * This method modifies the given date object, converting it to the given
 * timezone if specified.
 * 
 * @param {Date} date the date object to round
 * @param {Number} intervalUnit a constant, integer index specifying an 
 *   interval, e.g. SimileAjax.DateTime.HOUR
 * @param {Number} timeZone a timezone shift, given in hours
 * @param {Number} multiple a multiple of the interval to round by
 * @param {Number} firstDayOfWeek an integer specifying the first day of the
 *   week, 0 corresponds to Sunday, 1 to Monday, etc.
 * @see SimileAjax.DateTime.roundDownToInterval
 */
SimileAjax.DateTime.roundUpToInterval = function(date, intervalUnit, timeZone, multiple, firstDayOfWeek, system) {
	var tSystem = (typeof system == 'undefined') ? "gregorian" : system;
    var originalTime = date.getTime();
    SimileAjax.DateTime.roundDownToInterval(date, intervalUnit, timeZone, multiple, firstDayOfWeek, tSystem);
    if (date.getTime() < originalTime) {
        date.setTime(date.getTime() + 
            SimileAjax.DateTime.gregorianUnitLengths[intervalUnit] * multiple);
    }
};

/**
 * Increments a date object by a specified interval, taking into
 * consideration the timezone.
 *
 * @param {Date} date the date object to increment
 * @param {Number} intervalUnit a constant, integer index specifying an 
 *   interval, e.g. SimileAjax.DateTime.HOUR
 * @param {Number} timeZone the timezone offset in hours
 */
SimileAjax.DateTime.incrementByInterval = function(date, intervalUnit, timeZone, system) {
	var tSystem = (typeof system == 'undefined') ? "gregorian" : system;
	timeZone = (typeof timeZone == 'undefined') ? 0 : timeZone;

	var timeShift = timeZone * 
		SimileAjax.DateTime.gregorianUnitLengths[SimileAjax.DateTime.HOUR];

	var date2 = new Date(date.getTime() + timeShift);

	switch(intervalUnit) {
	case SimileAjax.DateTime.MILLISECOND:
	case SimileAjax.DateTime.SECOND:
	case SimileAjax.DateTime.MINUTE:
	case SimileAjax.DateTime.HOUR:
	case SimileAjax.DateTime.DAY:
	case SimileAjax.DateTime.WEEK:
	case SimileAjax.DateTime.YEAR:
		SimileAjax.DateTime.setUnitDate(date2,SimileAjax.DateTime.getUnitDate(date2,intervalUnit,tSystem)+1,intervalUnit,tSystem);
		break;
	case SimileAjax.DateTime.MONTH:
		if ( tSystem != "ayoaron" ) {
			SimileAjax.DateTime.setUnitDate(date2,SimileAjax.DateTime.getUnitDate(date2,intervalUnit,tSystem)+1,intervalUnit,tSystem);
		}else{
			var mon = SimileAjax.DateTime.getUnitDate(date2,intervalUnit,tSystem);
			if ( mon == 10 ) {
				date2.setTime(date2.getTime()+15*SimileAjax.DateTime.ayoaronUnitLengths[SimileAjax.DateTime.DAY]);
			} else {
				SimileAjax.DateTime.setUnitDate(date2,SimileAjax.DateTime.getUnitDate(date2,intervalUnit,tSystem)+1,intervalUnit,tSystem);
			}
		}
		break;
	case SimileAjax.DateTime.DECADE:
	case SimileAjax.DateTime.CENTURY:
	case SimileAjax.DateTime.MILLENNIUM:
		var age = SimileAjax.DateTime.getUnitDate(date2,SimileAjax.DateTime.AGE,tSystem);
		SimileAjax.DateTime.setUnitDate(date2,SimileAjax.DateTime.getUnitDate(date2,intervalUnit,tSystem)+1,intervalUnit,tSystem);
		if ( tSystem == "ayoaron" ) {
			var age2 = SimileAjax.DateTime.getUnitDate(date2,SimileAjax.DateTime.AGE,tSystem);
			if ( age2 > age ) {
				var offset = 9913 * SimileAjax.DateTime.ayoaronUnitLengths[SimileAjax.DateTime.YEAR];
				date2.setTime(-offset);
				SimileAjax.DateTime.setUnitDate(date2,age2,SimileAjax.DateTime.AGE,tSystem);
			}
		}
		break;
	}

	date.setTime(date2.getTime() - timeShift);
};

/**
 * Returns a new date object with the given time offset removed.
 *
 * @param {Date} date the starting date
 * @param {Number} timeZone a timezone specified in an hour offset to remove
 * @return {Date} a new date object with the offset removed
 */
SimileAjax.DateTime.removeTimeZoneOffset = function(date, timeZone) {
    return new Date(date.getTime() + 
        timeZone * SimileAjax.DateTime.gregorianUnitLengths[SimileAjax.DateTime.HOUR]);
};

/**
 * Returns the timezone of the user's browser.
 *
 * @return {Number} the timezone in the user's locale in hours
 */
SimileAjax.DateTime.getTimezone = function() {
    var d = new Date().getTimezoneOffset();
    return d / -60;
};
