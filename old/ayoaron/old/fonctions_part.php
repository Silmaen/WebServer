<?PHP

require("fonctions_centrales.php");

/**
 *  fonction de dessin de la partie centrale du document
 */
function draw_centre($page){
	if ($_GET["typ"]!="") $_POST["typ"]=$_GET["typ"];
	if ($_GET["obj"]!="") $_POST["obj"]=$_GET["obj"];
?>
			<div class="centre">
				<div class="colonnel">
<?PHP 	draw_colonne_gauche($page);?>
				</div>
				<div class="colonnem">
				<!--[if lte IE 9 ]>
					<H1>Attention: votre navigateur est trop merdique pour afficher correctement la plupart des éléments de cette page.</H1>
					<H1>Veuillez utiliser Internet Exploiteur version 10 ou suppéreur, ou utiliser un vrai navigateur.</H1>
				<![endif]-->
<?PHP 	draw_colonne_centrale($page);?>
				</div>
				<div class="colonner">
<?PHP 	draw_colonne_droite($page);?>
				</div>
			</div>
<?PHP
}
 

/**
 *  fonction de dessin de l'entête de la page
 */
function draw_header(){?>
			<!-- dessin du bloc d'entête -->
			<div class="top">
				<!-- cadre de titre -->
				<header class="bandeau" >
					<div id="blocgauche">
					</div>
					<div id="connection">
						<?PHP if ($_SESSION['login']!="") { ?>
							<p>Bienvenu <?PHP echo $_SESSION['nom']; ?> </p>
							<form method="post" action="<?PHP echo $_SERVER['PHP_SELF']; ?>">
								<input type="submit" name="envoi" value="logout" />
							</form>
						<?PHP } else { ?>
							<p>Salut utilisateur inconnu</p>
							<p>connexion: <form method="post" action="<?PHP echo $_SERVER['PHP_SELF']; ?>"><label for="login">Login:</label><input type="text" name="login"/>
											<label for="password">Password:</label><input type="password" name="pasword"/>
											<input type="submit" name="envoi" value="connexion"/>
											</form><p>
						<?PHP } ?>
					</div>
					<div id="infonav" >
						<p>Attention, l'affichage de ce site nécéssite un navigateur supportant HTML5.</p>
						<p>testé sur:
							<ul>
								<li><a href="http://www.google.com/chrome?hl=fr" title="Le navigateur de google"><img src="http://www.google.com/images/icons/product/chrome-16.png" height="10">Google Chrome 15.0</a></li>
								<li><a href="http://www.mozilla.org/fr/firefox/new/" title="Le navigateur de Mozilla Firefox"><img src="http://people.mozilla.com/~faaborg/files/shiretoko/firefoxIcon/firefox-16-noshadow.png" height="10">Firefox 8.0</a></li>
							</ul>
						</p>
					</div>
				</header>
				<!-- barre de navigation horizontale -->
				<nav class="adress">
					<ul id="tabnav">
						<li><a href="news.php" title="Les news du projet"> News </a></li>
						<li><a href="histoire.php" title="L'histoire du monde d'Ayoaron"> Histoire </a></li>
						<li><a href="langue.php" title="Apprendre à parler ayoaron"> Langue </a></li>
						<li><a href="developpements.php" title="La page des développement du jeu"> Developpements </a></li>
						<?PHP if ($_SESSION['acred']>0) { ?><li><a href="univers.php" title="L'univers d'Ayoaron"> Univers </a></li>
						<li><a href="timeline.php" title="L'histoire en ligne de temps"> Timeline </a></li><?PHP }?>
						
					</ul>
				</nav>
			</div>
<?PHP
}

/**
 *  fonction de dessin du pied de la page
 */
function draw_footer(){?>
			<footer class="pied">
				Design : <adress class="author"><em class="fn">Argawaen</em></adress>
				<p>
					powered by :
					<img src="img/HTML5b-logo.png" height=50 />
					<img src="img/powered_small.gif" width=211 height=50 />
				</p>
			</footer>
<?PHP
}

?>