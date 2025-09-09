/**
 * @jest-environment jsdom
 */

//import { initializeAuthForms } from './auth';

// Helper pour flusher les promesses en attente dans les tests
// Remplacement de setImmediate par setTimeout pour la compatibilité avec jsdom
const flushPromises = () => new Promise(resolve => setTimeout(resolve, 0));

// --- Mocks Globaux ---

// Mock de l'objet Http qui sera attaché à window
const mockHttpRequest = jest.fn();
(window as any).Http = {
  request: mockHttpRequest,
};

// Mock de la redirection
const mockLocationAssign = jest.fn();
Object.defineProperty(window, 'location', {
  value: {
    assign: mockLocationAssign,
  },
  writable: true,
});


describe('Authentication Forms Logic (auth.ts)', () => {

  beforeEach(() => {
    // Nettoyer les mocks avant chaque test
    mockHttpRequest.mockClear();
    mockLocationAssign.mockClear();

    // Préparer le DOM mocké avec les formulaires
    document.body.innerHTML = `
      <form id="web-login-form">
        <input name="email" value="test@example.com" />
        <input name="password" value="password123" />
        <button type="submit">Login</button>
        <div class="message-area"></div>
      </form>
      <form id="web-signup-form">
        <input name="email" value="new@example.com" />
        <input name="password" value="newPassword123!" />
        <input name="full_name" value="New User" />
        <button type="submit">Sign Up</button>
        <div class="message-area"></div>
      </form>
    `;

    // Initialiser les gestionnaires d'événements sur le DOM mocké
    initializeAuthForms();
  });

  // --- Tests pour le formulaire de Connexion ---

  describe('Login Form', () => {
    it('should call login API with correct credentials and redirect on success', async () => {
      const loginForm = document.querySelector<HTMLFormElement>('#web-login-form')!;
      
      // Mock de la réponse API réussie
      const mockSuccessResponse = {
        ok: true,
        json: () => Promise.resolve({
          access_token: 'fake-token',
          token_type: 'bearer',
          user: { id: '123', email: 'test@example.com', role: 'user' },
        }),
      };
      mockHttpRequest.mockResolvedValue(mockSuccessResponse);

      // Simuler la soumission du formulaire
      loginForm.dispatchEvent(new Event('submit'));

      // Attendre que les promesses (fetch, .json()) se résolvent
      await flushPromises();

      // Vérifier que l'API a été appelée avec les bonnes données
      expect(mockHttpRequest).toHaveBeenCalledWith('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          email: 'test@example.com',
          password: 'password123',
        }),
      });

      // Vérifier la redirection
      expect(mockLocationAssign).toHaveBeenCalledWith('/session');
    });

    it('should display an error message on login failure', async () => {
        const loginForm = document.querySelector<HTMLFormElement>('#web-login-form')!;
        const messageEl = loginForm.querySelector<HTMLElement>('.message-area')!;

        // Mock de la réponse API en échec
        const mockErrorResponse = {
            ok: false,
            status: 401,
            json: () => Promise.resolve({ detail: 'Identifiants invalides' }),
        };
        mockHttpRequest.mockResolvedValue(mockErrorResponse);

        // Simuler la soumission
        loginForm.dispatchEvent(new Event('submit'));
        await flushPromises();

        // Vérifier l'appel API
        expect(mockHttpRequest).toHaveBeenCalledTimes(1);
        
        // Vérifier que le message d'erreur est affiché
        expect(messageEl.textContent).toBe('Identifiants invalides');
        expect(messageEl.className).toContain('err');

        // Vérifier qu'il n'y a pas de redirection
        expect(mockLocationAssign).not.toHaveBeenCalled();
    });
  });

  // --- Tests pour le formulaire d'Inscription ---

  describe('Signup Form', () => {
    it('should call signup API and redirect on success', async () => {
      const signupForm = document.querySelector<HTMLFormElement>('#web-signup-form')!;

      // Mock de la réponse API réussie
      const mockSuccessResponse = {
        ok: true,
        json: () => Promise.resolve({ message: 'Inscription réussie' }),
      };
      mockHttpRequest.mockResolvedValue(mockSuccessResponse);

      // Simuler la soumission
      signupForm.dispatchEvent(new Event('submit'));
      await flushPromises();

      // Vérifier l'appel API
      expect(mockHttpRequest).toHaveBeenCalledWith('/api/v1/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          email: 'new@example.com',
          password: 'newPassword123!',
          full_name: 'New User',
        }),
      });

      // Vérifier la redirection
      expect(mockLocationAssign).toHaveBeenCalledWith('/');
    });
  });
});

  // --- Tests pour le formulaire Mot de passe oublié ---
describe('Forgot Password Form', () => {
  beforeEach(() => {
     mockLocationAssign.mockClear(); // <--- important !
    document.body.innerHTML = `
      <form id="web-forgot-form">
        <input name="email" value="reset@example.com" />
        <button type="submit">Reset</button>
        <div class="message-area"></div>
      </form>
    `;
    initializeAuthForms();
  });

  it('should call forgot password API and show success message', async () => {
    const forgotForm = document.querySelector<HTMLFormElement>('#web-forgot-form')!;
    const messageEl = forgotForm.querySelector<HTMLElement>('.message-area')!;

    // Espionner reset()
    const resetSpy = jest.spyOn(forgotForm, "reset");

    // Mock succès
    const mockSuccessResponse = {
      ok: true,
      json: () => Promise.resolve({ message: 'Email envoyé avec succès' }),
    };
    mockHttpRequest.mockResolvedValue(mockSuccessResponse);

    forgotForm.dispatchEvent(new Event('submit'));
    await flushPromises();

    // Vérifier l’appel API
    expect(mockHttpRequest).toHaveBeenCalledWith('/api/v1/auth/request-password-reset', expect.any(Object));

    // Vérifier message affiché
    expect(messageEl.textContent).toBe('Email envoyé avec succès');
    expect(messageEl.className).toContain('ok');

    // Vérifier reset du formulaire
    expect(resetSpy).toHaveBeenCalled();
  });

  it('should show error message if API fails', async () => {
    const forgotForm = document.querySelector<HTMLFormElement>('#web-forgot-form')!;
    const messageEl = forgotForm.querySelector<HTMLElement>('.message-area')!;

    // Mock erreur
    const mockErrorResponse = {
      ok: false,
      status: 400,
      json: () => Promise.resolve({ detail: 'Adresse email introuvable' }),
    };
    mockHttpRequest.mockResolvedValue(mockErrorResponse);

    forgotForm.dispatchEvent(new Event('submit'));
    await flushPromises();

    // Vérifier message erreur
    expect(messageEl.textContent).toBe('Adresse email introuvable');
    expect(messageEl.className).toContain('err');

    // Vérifier qu'il n'y a PAS de redirection
    expect(mockLocationAssign).not.toHaveBeenCalled();
  });
});
