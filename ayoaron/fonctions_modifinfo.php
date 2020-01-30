<?PHP

function draw_colone_gauche_modifinfo(){

}

function draw_colone_droite_modifinfo(){

}

function draw_colone_centre_modifinfo(){
	if ($_SESSION['login']=="") header('new.php');
	require_once("fonctions_bd.php");
	$idcom=connexion_bd();
	$affform =1;
	$requete = "UPDATE `user` SET ";
	if ($_POST['envoi']=="update") {
		if ($_POST['oldpasswd']=="") { ?>
					<p>Veuillez saisir votre password.</p><?PHP 
		} else {
			$passwd=md5($_POST['oldpasswd']);
			if ($passwd!=$_SESSION['password']) { ?>
					<p>Erreur password incorrect.</p><?PHP 
					echo $passwd."\n";
					echo $_SESSION['password']."\n";
					echo md5("cyanide")."\n";
			} else {
				if ($_POST['password']!="") {
					if ($_POST['password']!=$_POST['passwordcfirm']) { ?>
					<p>Erreur: Le password et sa confirmation ne concordent pas!</p><?PHP 
					} else {
						$requete = $requete.'`password`="'.md5($_POST['password']).'" ';
						$affform =0;
					}
				}
				if ($_POST['nom']!="") {
					$requete = $requete.'`nom`="'.$_POST['nom'].'" ';
					$affform =0;
				}
				if ($_POST['prenom']!="") {
					$requete = $requete.'`prenom`="'.$_POST['prenom'].'" ';
					$affform =0;
				}
				if ($_POST['adresse']!="") {
					$requete = $requete.'`adresse`="'.$_POST['adresse'].'" ';
					$affform =0;
				}
				if ($_POST['email']!="") {
					$requete = $requete.'`email`="'.$_POST['email'].'" ';
					$affform =0;
				}
			}
		}
		$requete = $requete." WHERE `id`=".$_SESSION['ID'];
		if ($affform==0) {
			$sql=mysqli_query($idcom,$requete);
			if (!$sql) { ?>
					<p>Erreur dans la base mysql.</p><?PHP 
					echo "<p>Requete: /\\".$requete."/\\</p>";
					echo "<p>".mysqli_error()."</p>";
			} else { ?>
					<p></p><?PHP
			}
		}
	}
	if ($affform!=0) { ?>
					<p>Vous pouvez saisir ici les données mises à jour de votre profil.</p>
					<p>Laissez vide les case qu'il n'est pas besoin de modifier.</p>
					<p>Pour changer vos informations, il est nécessaire de rentrer à nouveau votre mot de passe dans le chmap 'Password'.</p>
					<form method="post" action="<?PHP echo $_SERVER['PHP_SELF']; ?>">
						<table>
							<tr><td>                                                  </td><td>                                                       </td><td>  Valeurs actuelles:               </td></tr>
							<tr><td> <label for="oldpasswd">Password:        </label> </td><td> <input type="password" name="oldpasswd"            /> </td><td>                                   </td></tr>
							<tr><td> <label for="password">Nouveau password: </label> </td><td> <input type="password" name="password"             /> </td><td>                                   </td></tr>
							<tr><td> <label for="passwordcfirm">Confirme:    </label> </td><td> <input type="password" name="passwordcfirm"        /> </td><td>                                   </td></tr>
							<tr><td> <label for="login">Nom:                 </label> </td><td> <input type="text"     name="nom"                  /> </td><td><?PHP echo $_SESSION['nom']; ?>    </td></tr>
							<tr><td> <label for="login">Prénom:              </label> </td><td> <input type="text"     name="prenom"               /> </td><td><?PHP echo $_SESSION['prenom']; ?> </td></tr>
							<tr><td> <label for="adresse">Addresse:          </label> </td><td> <input type="text"     name="adresse"              /> </td><td><?PHP echo $_SESSION['adresse']; ?></td></tr>
							<tr><td> <label for="email">E-mail:              </label> </td><td> <input type="text"     name="email"                /> </td><td><?PHP echo $_SESSION['email']; ?>  </td></tr>
							<tr><td>                                                  </td><td> <input type="submit"   name="envoi" value="update" /> </td><td>                                   </td></tr>
						</table> 
					</form>
	<?PHP }
	mysqli_close($idcom);
}

?>