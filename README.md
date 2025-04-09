Ilie Lucian-Alexandru 331CB
Tema 1 ASC

Am facut acest readme pentru a descrie general cum functioneaza aplicatia implementata, explicand rolurile fiecarui fisier si componenta implementate. Pe langa cele 4 fisiere pe care le aveam de implementat din schelet, am creat si niste teste separate (unittesturi din python) pentru testarea unitara a functiilor. Astfel, folosind acest modul din python, ne putem asigura ca orice modificare adusa aplicatiei nu va afecta negativ si poate fi verificata automat.

In implementare am urmatoarele fisiere:
1. routes.py: 
In acest fisier sunt definite toate rutele API pe care le expune aplicatia Flask pentru procesarea datelor pe care le avem. Fiecare ruta initiaza un job asincron si returneaza rezultatele de care avem nevoie. Totodata, tot aici leg si functiile pe care le implementez de cele definite in data_ingestor, acestea fiind totodata adaugate si in Threadpool si inregistrare in logging:

Functii implementate:
/api/post_endpoint -> Primeste un payload de JSON si il returneaza
/api/get_results/ -> Verificam daca jobul este in curs. Daca nu, returnez rezultatul jobului respectiv, daca fisierul de rezultate exista
/api/states_mean -> Calculeaza media valorilor pentru o intrebare, grupat in functie de fiecare stat
/api/state_mean -> Asemanator cu states_mean, doar ca aici calculez media pentru o intrebare intr un singur stat
/api/best5 -> Returneaza cele mai bune 5 state (cu cele mai bune valori) pentru o intrebare anume
/api/worst5 -> La fel ca la best5, doar ca aici returnez cele mai slabe 5 state pentru o intrebare
/api/global_mean -> Calculeaza media globala pentru o intrebare anume
/api/diff_from_mean -> Calculeaza, pentru fiecare stat, diferenta fata de media globala pentru un anumit lucru
/api/state_diff_from_mean -> Calculeaza diferenta unui anumit stat fata de media globala
/api/mean_by_category -> Calculeaza media valorilor grupate pe categorii
/api/state_mean_by_category -> La fel ca la mean, doar ca aici este filtrat pentru un stat specific
/api/graceful_shutdown -> Aici se initiaza oprirea controlata a serverului dupa terminarea tuturor joburilor active
/api/jobs -> Functia listeaza toate joburile care sunt create si statusul lor
/api/num_jobs -> Functia returneaza numarul de joburi care sunt inca in executie
/ si /index -> aici avem pagina principala care listeaza toate rutele disponibile ale API

De asemenea, in fiecare functie am verificat, folosind o variabila accept din init, dac acumva s a dat shutdown, pentru a nu mai putea primi joburi noi, dar totusi sa se poata termina cele care sunt incepute deja.

Pe scurt, marea majoritate a rutelor folosesc mecanismul asincron al aplicatiei, adaugand taskuri in coada de executie. Pentru fiecare job se va retine un id si va fi salvat in fisierele JSON din directorul results. Tot aici, am adaugat periodic mesaje in logger pentru a putea vedea ceea ce se intampla si a putea face debugging mai usor acolo unde a fost nevoie. Toate acestea le puteam vedea in fisierul webserver.log.

2. task_runner.py:
In acest fisier am implementat practic un sistem de executare paralela a taskurilor, folosindu-ma de un threadpool. Acesta este responsabil pentru gestionarea cozii de joburi, distribuirea acestora catre threaduri si salvarea si afisarea rezultatelor in fisierele json.

Functionalitati implementate:
Clasa ThreadPool:
Dupa cum ziceam, clasa aceasta este responsabila pentru gestionarea threadurilor si a cozii de executie. In __init__(), am initializat un pool de threaduri in functie de numarul de procesoare disponibile, urmand apoi in add_task sa adaug un nou task in coada, daca serverul este pornit. Tot aici returnez si job_id ul. Mai am functiile ajutatoare graceful_shutdown() (care initiaza oprirea controlata a threadurilor dupa ce s au terminat de facut toate taskurile curente), get_status(job_id) (care returneaza statusul curent al unui job {running, done, error sau invalid}), all_jobs() (care returneaza un dictionar cu toate joburile si statusul lor) si pending_jobs() (care returneaza cate joburi sunt inca in executie).

Clasa TaskRunner:
Este practic un thread individual care ruleaza in fundal si proceseaza taskuri din coada. In __init__(), primeste coada de taskuri, job_status, eventul de shutdown, loggerul si data ingestorul. Avem aici metoda run(), care executa taskurile pana cand serverul este inchis si coada este goala. Rezultatul fiecarui job este salvat intr un fisier json in results.

Am folosit aici daemon=True, care face  ca threadurile sa ruleze in fundal, astfel incat nu blocheaza oprirea aplicatiei.

3. data_ingestor.py
In acest fisier am implementat clasa DataIngestor, responsabila pentru citirea si procesarea datelor din fisierul csv dat. Mai departe, tot aici, am implementat mai multe metode pentru a calcula diverse medii pe baza cerintelor. Avem: 
filter_by_question(question) -> functia returneaza toate randurile care corespund unei anumite intrebari specifice
get_states_mean(question) -> functia calculeaza media valorilor (adica Data_Value) pentru fiecare stat in parte, pentru o intrebare data
get_state_mean(question, state)	-> calculeaza media pentru un anumit stat si intrebare
get_global_mean(question) -> calculeaza media globala pentru o intrebare anume
get_mean_by_category(question, state=None) -> returneaza media pe categorii de stratificare pentru o intrebare anume

4. __init__.py
In acest fisier am initializat aplicatia Flask si am configurat loggerul, am incarcat datele si sistemul de gestionare al taskurilor.
Am creat in prima faza directorul results, unde vor fi salvate rezultatele joburilor in fisiere .json. In continuare, am configurat loggerul,
care scrie intr un fisier webserver.log. Acesta foloseste formatul UTC conform cerintei. Este initializata apoi aplicatia Flask si se ataseaza
loggerul. Tot aici am creat o variabila accept, pe care aici o fac true, care se va face false in graceful_shutdown pentru a verifica daca se inchide
serverul chiar daca mai are chestii de facut. Se încarcă fișierul nutrition_activity_obesity_usa_subset.csv prin clasa DataIngestor, care va fi 
disponibilă global prin webserver.data_ingestor. POrnesc apoi threadpool ul, care va fi si el disponibil prin webserver.tasks_runner. 
In ultima parte, am initializat job counterul, care este folosit pentru a genera id urile unice ale fiecarui job in parte.
In concluzie, acest fisier este practic punctul de start al aplicatiei si centralizeaza aici pornirea si initializarea tuturor componentelor necesare 
functionarii aplicatiei. 

5. TestWebserver.py
Aici este fisierul unde am creat unittesturile pentru validarea corectitudinii si functionarii optime a tuturor rutelor din API definite in routes.
Practic, prin aceste teste ne asiguram ca datele sunt procesate corect si ca rezultatele intoarse sunt cele asteptate pentru o anumite intrebare si un
set de date dat.
Am creat clasa TestWebserver care este mostenita din unittest.Testcase. AIci am initializat un client Flask si fisierul csv din aplicatie si am creat 
o suita de 15 teste unitare pentru fiecare endpoint din routes.py prin care se verifica ca serverul returneaza structura corecta (de exemplu ca job_id
este prezent si corect calculat si retinut).
