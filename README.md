## Data Master: Aggron - plataforma E2E de governança de dados
By: Fabiana Andrade Barroso

Trilha: Engenharia de Dados

Esse case tem como objetivo apresentar uma plataforma de dados capaz de oferecer integração completa abrangendo o primeiro momento de modelagem e dicionarização da tabela, concepção de contratos de dados, criação do metadado no lake e integração com catálogo de governança.

A solução foi desenvolvida com conhecimentos interdiciplinares de engenharia de sofware, engenharia de dados e computação em nuvem. Além disso, priorizou-se a utlização de ferramentas open-source, de modo que facilitasse a reprodutibilidade. 


## Objetivos com a solução:

Na organização observo oportunidades que podem melhor a jornada do usuário, entre elas:
- Oferecer uma interface única e governada para criação e edição de tabelas no lake;
- Aplicar contrato de dados para todas tabelas do ambiente, de modo que cada base tenha SLAs bem definidos desde sua criação.
- Consumidores dos dados serem notificados em caso de alteração em tabela consumida
- 

# Desenho de Arquitetura
![alt text](figures/case_desenho.png)

*Fun-fact*: O nome "Aggron" vem de um pokémon. Ele foi escolhido para representar a plataforma depois de muitas tentativas de escolher um nome legal...

<img src="figures/image-1.png" alt="Aggron Pokémon" width="150">

### **Explicação dos Componentes**: ###
#### **Frontend** ####

A solução oferece uma interface responsável por permitir que usuários criem, editem e deletem tabelas do data lake. Por meio de uma interface amigável, que tanto o usuário de negócio, quanto engenheiros, podem utilizar, o usuário pode submeter suas solicitações. 

Todas as solicitações passam por um processo de aprovação, dessa forma, o owner da sigla/technical lead precisa aprovar a implantação. Após aprovação, a implementação segue de forma automática.


A implementação foi realizada com React 18 (SPA) e TypeScript, utilizando Vite 5 como servidor de desenvolvimento e ferramenta de build.

A navegação é feita com react-router-dom e o gerenciamento de estado de dados remotos com @tanstack/react-query.

O frontend consome APIs REST do backend via fetch, com URLs configuradas por variáveis de ambiente (`VITE_AUTH_SERVICE_URL`, `VITE_INGESTION_SERVICE_URL`, `VITE_APPROVAL_SERVICE_URL`).

A autenticação é baseada em JWT, com rotas protegidas no frontend e sessão persistida no navegador.

![alt text](figures/image.png)

#### **LDAP Server** ###
A autenticação na plataforma é gerenciada a partir de um servidor LDAP.
No LDAP implementado, foi cadastrado previamente algumas siglas e usuários, assim sendo os usuários so conseguem abrir solicitações para tabelas da própria sigla, bem como os aprovadores (owners) das siglas são consumidos com base no que está cadastrado no LDAP.

<img src="figures/ldap_logica.png" alt="Aggron Pokémon" width="400">



#### **Camada de microserviços**
todotodo
#### **Processamento streaming**
todotodo
#### **CI/CD**
todotodo