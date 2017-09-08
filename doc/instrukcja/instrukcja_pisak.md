<div style="text-align:center"></div>
###Instrukcja instalacji i uruchomienia PISAKa w wersji Budzik

####A. Instalacja oraz ustawienia systemu operacyjnego

1. Wchodzimy w ustawienia BIOSU i tam:
     * przywracamy ustawienia domyślne (mogą być OS Optimized)
     * wyłączamy Secure Boot
     * wyłączamy Network Boot
     * włączamy możliwość uruchamiania z USB
  
2. Instalujemy Ubuntu 16.04 z domyślnymi ustawieniami, w języku angielskim (układ klawiatury i strefa czasowa powinny pozostać polskie).

3. Ustawiamy w BIOSie uruchamianie z wewnętrznego dysku twardego.

4. Uruchamiamy zainstalowane Ubuntu i włączamy terminal (*Ctrl+Alt+t*).

5. Aktualizujemy system wpisując w terminalu komendy:

    <pre><code>sudo apt-get update
sudo apt-get upgrade
sudo apt-get dist-upgrade</code></pre>
    
6. Instalujemy git-a wpisując w terminalu komendę:

    <pre><code>sudo apt-get install git</code></pre>

</br>

####B. Instalacja oprogramowania PISAK ###
1. Przechodzimy do katalogu domowego

    <pre><code>cd ~</code></pre>

2. Pobieramy PISAKa w wersji budzik
    
    <pre><code>git clone https://github.com/BrainTech/pisak.git</code></pre>
    
    podając swój login i hasło.
    
3. Instalujemy PISAKa
    
    <pre><code>cd pisak
    bash instalujpisak.sh</code></pre>

4. Wylogowujemy i logujemy ponownie

5. W ustawieniach systemu (System Settings -> Power):

    * odznaczamy opcję *Dim screen when inactive* 
    * ustawiamy opcję *Blank screen* na *Never*
    * ustawiamy opcję *Automatic suspend* na *OFF*

6. Konfigurujemy PISAKa

    Stworzony na pulpicie skrót 'Konfiguracja PISAKa' umożliwia wejście w panel ustawień aplikacji.

7. Uruchamiamy aplikację

    PISAK uruchomi się po kliknięciu w znajdujący się na pulpicie skrót 'PISAK' lub wpisując polecenie pisak w wyszukiwarce Dash. Ponadto PISAKa można uruchomić wpisując w terminalu komendę pisak.
