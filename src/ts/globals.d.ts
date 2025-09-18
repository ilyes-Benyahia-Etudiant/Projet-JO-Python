export {};

declare global {
  interface Window {
    CSRF_TOKEN?: string;
    Admin: {
      refresh: () => void | Promise<void>;
      showOffres: () => Promise<void>;
      showCommandes: () => Promise<void>;
      showUsers: () => Promise<void>;
      editUser: (id: string, currentEmail?: string) => Promise<void>;
      deleteUser: (id: string) => Promise<void>;
      editCommande: (id: string, currentStatus?: string, currentPrice?: string | number) => Promise<void>;
      deleteCommande: (id: string) => Promise<void>;
    };
  }
}