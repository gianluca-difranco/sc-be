# Regole per l'Intelligenza Artificiale (AI Rules)

Queste regole **DEVONO ESSERE LETTE E RISPETTATE SEMPRE** in tutte le conversazioni e task correnti e future.

## Gestione Variabili d'Ambiente e File `.env`
1. **DIVIETO ASSOLUTO DI LEGGERE I FILE `.env`**: È severamente vietato utilizzare qualsiasi strumento (`view_file`, `cat`, o script) per leggere il contenuto dei file `.env` presenti nei vari repository. I file `.env` contengono segreti e informazioni sensibili e non devono essere esposti o analizzati.
2. **DIVIETO ASSOLUTO DI SCRIVERE O MODIFICARE I FILE `.env`**: Non utilizzare strumenti per sovrascrivere o inserire dati nei file `.env`. 
3. **Utilizzo di `.env.example`**: Per qualsiasi configurazione riguardante le variabili d'ambiente, fare riferimento esclusivo o aggiornare i file `.env.example`. Chiedere all'utente di applicare le modifiche sul suo file `.env` locale in autonomia.

*L'obiettivo di queste direttive è garantire la massima sicurezza evitando leak accidentali di credenziali, chiavi API o altri dati sensibili.*

## Versioning e Git
1. **DIVIETO ASSOLUTO SUI COMANDI GIT**: È severamente vietato eseguire qualsiasi operazione tramite il tool `run_command` (o affini) che coinvolga il sistema di controllo di versione Git (es. `git commit`, `git push`, `git add`, `git pull`, `git rebase` ecc.). 
2. **Gestione del Codice**: Ogni modifica al codice o ai file di configurazione deve limitarsi alla sola scrittura dei file in locale. La responsabilità del versioning, dei commit e dei push sul repository remoto è esclusivamente a carico dell'utente umano.
