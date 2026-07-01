\# INFRA - Serveur d'inférence IA



\## Choix technique



Le serveur d'inférence choisi est \*\*Ollama\*\*.



Ce choix a été motivé par :



\- une installation rapide ;

\- une API REST intégrée ;

\- une compatibilité native avec les modèles Phi ;

\- une mise en œuvre simple adaptée à un hackathon.



\---



\## Modèle déployé



Le modèle utilisé est :



\- \*\*phi3.5\*\* comme modèle de base ;

\- \*\*techcorp-finance\*\* comme modèle personnalisé.



Le modèle a été spécialisé pour répondre aux besoins des analystes financiers de TechCorp Industries grâce à un prompt système dédié.



\---



\## Paramètres d'inférence



Les paramètres suivants ont été configurés :



```text

temperature = 0.2

top\_p = 0.9

num\_predict = 512

