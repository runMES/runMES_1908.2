
python3 manage.py runscript run_log_runMES&
echo "*** started start_log_runMES ***"
python3 manage.py runscript run_CFM_job&
echo "*** started start_CFM ***"
python3 manage.py runscript run_lot_job&
echo "*** started lot_job ***"
python3 manage.py runscript run_eap_if&
echo "*** stated EAP I/F ***"
uwsgi ./uwsgi.ini
echo "*** stated uwsgi ***"
