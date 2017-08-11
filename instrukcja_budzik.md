<div style="text-align:center"></div>
## Instrukcja instalacji i uruchomienia PISAKa w wersji Budzik #

---

### A. Instalacja oraz ustawienia systemu operacyjnego ###

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

7. W ustawieniach systemu (System Settings -> Power Management):
     * wyłączamy gaszenie ekranu i usypianie komputera przy nieaktywności,
     * wyłączamy gaszenie ekranu przy niskim stanie baterii i przy zamknięciu pokrywy.

8. W ustawieniach systemu (System Settings -> Brightness & Lock):
    * odznaczamy opcję *Dim screen to saver power* 
    * ustawiamy opcję *Turn screen off when inactive for* na *Never*
    * ustawiamy opcję *Lock* na *OFF*
    
### B. Instalacja oprogramowania PISAK ###
1. Przechodzimy do katalogu domowego

    <pre><code>cd ~</code></pre>

2. Pobieramy PISAKa w wersji budzik
    
    <pre><code>git clone -b budzik --single-branch https://git.braintech.pl/brain/pisak.git</code></pre>
    
    Podając:
      * username: budzik
      * password: budzik
    
3. Instalujemy PISAKa:
    
    <pre><code>cd pisak
    bash instalujpisak.sh</code></pre>

4. Konfigurujemy PISAKa:

    Stworzony na pulpicie skrót 'Konfiguracja PISAKa' umożliwia wejście w panel ustawień aplikacji

5. Uruchamiamy aplikację

    PISAK uruchomi się po kliknięciu na skrót 'PISAK' na pulpicie, bądź poprzez wyszkukiwarkę systemową.
    Możliwe jest też uruchamianie bezpośrednio z terminala poprzez wpisanie polecenia 'pisak'

