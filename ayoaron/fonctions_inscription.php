<?PHP

require_once("fonctions_bd.php");

function draw_colone_gauche_inscription(){
}

function draw_colone_droite_inscription(){
}

function draw_colone_centre_inscription() {
	require_once("fonctions_bd.php");
	$idcom=connexion_bd();
	?>
					<h2>Page d'inscription aux données.</h2>
	<?PHP
		$valide = 0;
		if ($_POST['envoi']=="valider") {
			$valide = 1;
			// vérification du password
			if ($_POST['password'] != $_POST['passwordcfirm'] ) {
				$valide = 0; ?>
					<p> Erreur: le password et sa confirmation ne coïncident pas.</p> <?PHP
			} else {
				if (strlen($_POST['password'])<6) {
					$valide = 0; ?>
					<p> Erreur: le password est invalide, il doit comporté au moins 6 caracètes.</p> <?PHP
				}
			}
			// vérification du login
			if (($_POST['login'] == "" )&&(strlen($_POST['login'])<6)) {
				$valide = 0; ?>
					<p> Erreur: le login est incorrect, il doit comporté au moins 6 caracètes.</p> <?PHP
			} else {
				$nblog = mysqli_num_rows(mysqli_query($idcom,"SELECT * FROM `user` WHERE `login`= '".$_POST['login']."'"));
				if ($nblog != 0) {
					$valide = 0; ?>
					<p> Erreur: le login est déjà utilisé, veuillez en choisir un autre.</p> <?PHP
				}
			}
			// vérification des nom et prénom
			if ((strlen($_POST['nom']) < 3 )||(strlen($_POST['prenom']) < 3)) {
				$valide = 0; ?>
					<p> Erreur: veuillez entrer un nom et un prénom corrects.</p> <?PHP
			}
			// vérification de l'adresse
			if ((strlen($_POST['adresse']) < 10 )) {
				$valide = 0; ?>
					<p> Erreur: veuillez entrer une adresse correcte.</p> <?PHP
			}
			// vérification de l'emeil
			if (!preg_match("#^(([a-z0-9!\#$%&\\\'*+/=?^_`{|}~-]+\.?)*[a-z0-9!\#$%&\\\'*+/=?^_`{|}~-]+)@(([a-z0-9-_]+\.?)*[a-z0-9-_]+)\.[a-z]{2,}$#i",$_POST['email'])) {
				$valide = 0; ?>
					<p> Erreur: veuillez entrer une adresse email correcte.</p> <?PHP
			}
		}
	if ($valide==0){?>
					<p> Veuillez renseigner vos données personnelles.</p>
					<form method="post" action="<?PHP echo $_SERVER['PHP_SELF']; ?>">
						<table>
							<tr><td> <label for="login">Login:           </label> </td><td> <input type="text"     name="login"/>                 </td></tr>
							<tr><td> <label for="password">Password:     </label> </td><td> <input type="password" name="password"/>              </td></tr>
							<tr><td> <label for="passwordcfirm">Confirme:</label> </td><td> <input type="password" name="passwordcfirm"/>         </td></tr>
							<tr><td> <label for="login">Nom:             </label> </td><td> <input type="text"     name="nom"/>                   </td></tr>
							<tr><td> <label for="login">Prénom:          </label> </td><td> <input type="text"     name="prenom"/>                </td></tr>
							<tr><td> <label for="adresse">Addresse:      </label> </td><td> <input type="text"     name="adresse"/>               </td></tr>
							<tr><td> <label for="email">E-mail:          </label> </td><td> <input type="text"     name="email"/>                 </td></tr>
							<tr><td>                                              </td><td> <input type="submit"   name="envoi" value="valider"/> </td></tr>
						</table>
					</form>
	<?PHP } else {
	//maintenant il faut enregistrer l'utilisateur
		$login    = mysqli_real_escape_string($idcom,$_POST['login']);
		$password = md5($_POST['password']);
		$nom      = mysqli_real_escape_string($idcom,$_POST['nom']);
		$prenom   = mysqli_real_escape_string($idcom,$_POST['prenom']);
		//$adresse  = mysqli_real_escape_string($idcom,$_POST['adresse']);
		$adresse  = $_POST['adresse'];
		$email    = mysqli_real_escape_string($idcom,$_POST['email']);
		$id       = mysqli_num_rows(mysqli_query($idcom,'SELECT id FROM user')) +1 ;
		$datecrea = date("Y-m-d H:i:s");
		$typeuser = "user";
		$requete = 'INSERT INTO user (   id,       login,        password,       nom,         prenom,       adresse,         email, date_inscription, date_connexion, ip_connexion, accreditation, type_utilisateur, date_lastconn, ip_lastconn)
							VALUES   ('.$id.', "'.$login.'", "'.$password.'", "'.$nom.'", "'.$prenom.'", "'.$adresse.'", "'.$email.'", "'.$datecrea.'", "'.$datecrea.'", "0.0.0.0"     ,  1      , "'.$typeuser.'" , "'.$datecrea.'" ,"0.0.0.0")';
		$sql = mysqli_query($idcom,$requete);
		if ($sql == 0) { ?>
					<p>Une erreur est survenue lors de l'inscription.</p>
					<p><?PHP echo mysqli_error(); ?></p><?PHP
		} else { ?>
					<p>Félicitation, <?PHP $_POST['prenom'] ?>vous êtes maintenant enregistré.</p>
					<p>Vous pouvez maintenant vous connecter en utilisant votre login et password.</p> <?PHP
		}
	}
	mysqli_close($idcom);
}

?>