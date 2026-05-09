# TODO - Staff rendez-vous (validate) 

- [x] Empêcher l’accès à la page `staff_appointment_validate` pour le staff : rediriger vers `staff_appointment_edit`.
- [x] Mettre à jour `templates/staff/profile.html` pour supprimer le lien/bouton “Valider & Confirmer”.

- [ ] Vérifier manuellement : 
  - [ ] ouvrir `/staff/appointment/<id>/validate/` redirige vers `/staff/appointment/<id>/edit/`
  - [ ] le dashboard affiche bien “Modifier” et “Supprimer” uniquement.
- [ ] (optionnel) Exécuter les tests : `python manage.py test`.

