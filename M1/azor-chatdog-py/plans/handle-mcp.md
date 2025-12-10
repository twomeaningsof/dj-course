Oto plan wdrożenia obsługi serwera MCP do Twojej aplikacji chatbot'a w formacie Markdown.

### 1. Przygotowanie Środowiska
- [ ] **Instalacja zależności**: Dodanie biblioteki `mcp` do projektu (`pip install mcp`).
- [ ] **Weryfikacja serwera**: Upewnienie się, że lokalny serwer MCP jest wykonywalny i działa poprawnie poza aplikacją (np. przez `mcp-inspector` lub prosty skrypt testowy).

### 2. Nowy Moduł: `MCPHandler` (Wrapper)
Należy stworzyć klasę odpowiedzialną za komunikację z procesem serwera.
- [ ] **Transport stdio**: Implementacja uruchamiania serwera MCP jako podprocesu (subprocess) z komunikacją przez standardowe wejście/wyjście.
- [ ] **Inicjalizacja Sesji MCP**: Nawiązanie połączenia (handshake) przy starcie aplikacji.
- [ ] **Pobieranie Narzędzi**: Implementacja metody pobierającej listę narzędzi (`list_tools`) z serwera MCP.
- [ ] **Wywoływanie Narzędzi**: Implementacja metody `call_tool(name, arguments)`, która wysyła żądanie do serwera i zwraca wynik.
- [ ] **Clean-up**: Obsługa poprawnego zamykania procesu serwera przy wyjściu z aplikacji (np. w `atexit`).

### 3. Warstwa Tłumaczenia (Adapter Schematów)
Gemini i MCP używają nieco innych struktur do definicji funkcji.
- [ ] **Mapper JSON Schema -> Gemini**: Stworzenie funkcji konwertującej format narzędzi MCP (JSON Schema) na format akceptowany przez `genai.GenerativeModel` (obiekty `Tool` lub odpowiednie słowniki).

### 4. Modyfikacja `LLMClient` (Gemini)
- [ ] **Wstrzykiwanie Narzędzi**: Zaktualizowanie metody inicjalizującej model, aby przyjmowała przetłumaczoną listę narzędzi.
- [ ] **Konfiguracja Modelu**: Ustawienie parametru `tools` w konstruktorze `GenerativeModel`.

### 5. Przebudowa Pętli Głównej (Main Loop)
Zmiana logiki z liniowej (User -> AI) na cykliczną (User -> AI -> [Tool -> AI] -> User).
- [ ] **Detekcja `function_call`**: Sprawdzanie w odpowiedzi modelu (`response.parts`), czy zawiera żądanie wywołania funkcji.
- [ ] **Wykonanie i Feedback**:
    - Jeśli wykryto funkcję: wyświetlenie statusu (np. "Uruchamiam narzędzie: `list_sessions`...").
    - Wywołanie funkcji przez `MCPHandler`.
- [ ] **Zwrot Wyniku (Function Response)**: Przesłanie wyniku działania narzędzia z powrotem do modelu, aby mógł wygenerować końcową odpowiedź tekstową.
- [ ] **Obsługa Błędów Tooli**: Zabezpieczenie przed sytuacją, gdy serwer MCP zwróci błąd (model powinien otrzymać informację o błędzie, a aplikacja nie powinna się wyłączyć).

### 6. Bezpieczeństwo i UX
- [ ] **Zabezpieczenie Sesji**: Upewnienie się, że użycie narzędzia do usuwania sesji na *bieżącej* sesji nie spowoduje crashu aplikacji przy próbie zapisu historii.
- [ ] **Wizualizacja**: Dodanie kolorowania w terminalu dla logów z działania narzędzi (oddzielenie treści czatu od logów systemowych MCP).

---