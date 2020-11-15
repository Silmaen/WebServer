<?PHP
//On demarre les sessions
session_start();
/**
 * fonction de dessin du début de page
 */
function draw_entete_html(){?>
<!DOCTYPE html>
<html lang="fr" class="no-js">
	<head>
		<title>Projet Ayoaron</title>
		<meta charset="UTF-8" >
		<!-- les méta données -->
		<meta name="robots" content="index,follow" >
		<meta name="author" content="Morna Arran Argawaen">
		<meta name="keywords" content="jeux video, simulateur de vol, moteur 3D" >
		<!-- mon icone -->
		<link rel="shortcut icon" href="img/favicon.ico" />
		<!-- mon style css -->
		<link rel="stylesheet" href="theme.css" type="text/css" media="screen">
		<!--[if lte IE 9 ]><link href="theme_ie.css" rel="stylesheet" type="text/css" media="screen" /><![endif]-->
		<script type="text/javascript" charset="utf-8">
			function afficheimage (adresseimage, placeimage) {
				document.images[placeimage].src = adresseimage; 
			} 
		</script> 
		<!--[if lt IE 10]>
		<script src="http://html5shiv.googlecode.com/svn/trunk/html5.js"></script>
		<![endif]-->
	</head>
	<body>
		<div class="conteneur">
		<!-- debut page --><?PHP
}


function draw_entete_html_spe(){?>
<!DOCTYPE html>
<html lang="fr" class="no-js">
	<head>
		<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
		<title>
			Projet Ayoaron
		</title>
		<!--[if lte IE 9 ]><meta http-equiv="X-UA-Compatible" content="IE=9"><![endif]-->
		<!-- les méta données -->
		<meta name="robots" content="index,follow" />
		<meta name="date" content="2011-12-02T15:40:00+0200" />
		<meta name="author" content="Morna Arran Argawaen">
		<meta name="keywords" content="jeux video, simulateur de vol, moteur 3D" />
		<!-- mon icone -->
		<link rel="shortcut icon" href="img/favicon.ico" />
		<!-- mon style css -->
		<link rel='stylesheet' href='api/api.css' type='text/css' />
		<link rel="stylesheet" href="theme.css" type="text/css" media="screen">
		<!--[if lte IE 9 ]><link href="theme_ie.css" rel="stylesheet" type="text/css" media="screen" /><![endif]-->
		<script type="text/javascript" charset="utf-8">
			function afficheimage (adresseimage, placeimage) {
				document.images[placeimage].src = adresseimage; 
			} 
		</script> 
		<!--[if lt IE 10]>
		<script src="http://html5shiv.googlecode.com/svn/trunk/html5.js"></script>
		<![endif]-->
		<script type="text/javascript" charset="utf-8">
			Timeline_ajax_url="api/ajax/simile-ajax-api.js?bundle=false";
			Timeline_urlPrefix="api/js/";
		</script>
		<script src="api/js/timeline-api.js?timeline-use-local-resources=true&bundle=false" type="text/javascript"></script>
		<!--<script src="api/js/scripts/ayoaron-ages.js" type="text/javascript"></script>-->
		<style>.timeline-horizontal .timeline-date-label-em { font-size: 150%; height: 3em; font-weight: normal; }</style>
		<script type="text/javascript" charset="utf-8">
		var tl;
		function onLoad() {
			var eventSource = new Timeline.DefaultEventSource(0);
			var d = new Date(517, 5, 5);
			var bandInfos = [
				Timeline.createBandInfo({
					width:          "55%", 
					intervalUnit:   Timeline.DateTime.YEAR, 
					intervalPixels: 50,
					date:			d,
					dateSystem:		"ayoaron",
					eventSource:	eventSource
				}),
				Timeline.createBandInfo({
					overview:       true,
					eventSource:	eventSource,
					width:          "20%", 
					date:			d,
					dateSystem:		"ayoaron",
					intervalUnit:   Timeline.DateTime.CENTURY, 
					intervalPixels: 75
				}),
				Timeline.createBandInfo({
					overview:       true,
					eventSource:	eventSource,
					width:          "15%", 
					date:			d,
					dateSystem:		"ayoaron",
					intervalUnit:   Timeline.DateTime.MILLENNIUM, 
					intervalPixels: 100
				})
				,
				Timeline.createBandInfo({
					overview:       true,
					eventSource:	eventSource,
					width:          "10%", 
					date:			d,
					dateSystem:		"ayoaron",
					intervalUnit:   Timeline.DateTime.YEAR, 
					intervalPixels: 50
				})
			];
			bandInfos[1].syncWith = 0;
			bandInfos[1].highlight = true;
			bandInfos[0].labeller = new Timeline.AyoaronAgeDateLabeller("fr");
			bandInfos[1].labeller = new Timeline.AyoaronAgeDateLabeller("fr");
			bandInfos[2].syncWith = 1;
			bandInfos[2].highlight = true;
			bandInfos[2].labeller = new Timeline.AyoaronAgeDateLabeller("fr");
			bandInfos[3].syncWith = 0;
			bandInfos[3].highlight = true;
			tl = Timeline.create(document.getElementById("t1"), bandInfos, Timeline.HORIZONTAL);
			tl.loadJSON("jzonized.php?"+(new Date().getTime()),function(json, url){eventSource.loadJSON(json, url);});
		}
		function centerTimeline(year) {
			tl.getBand(0).setCenterVisibleDate(new Date(year,0,1));
		}
		
		var resizeTimerID = null;
		function onResize() {
			if (resizeTimerID == null) {
				resizeTimerID = window.setTimeout(function() {
					resizeTimerID = null;
					tl.layout();
				}, 500);
			}
		}
		
		</script>
	</head>
	<body onload="onLoad();" onresize="onResize();">
		<div class="conteneur">
	<!-- debut page --><?PHP
}

/**
 *  fonction de dession du pied de page html
 */
function draw_pied_html(){?>
		</div>
	</body>
</html>

<!-- fin page --><?PHP
}

?>