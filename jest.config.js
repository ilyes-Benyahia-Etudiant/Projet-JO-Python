/** @type {import('ts-jest').JestConfigWithTsJest} */
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  // Le chemin vers vos tests
  roots: ['<rootDir>/src/ts'],
  // Exclure les fichiers compilés du dossier de build
  modulePathIgnorePatterns: ['<rootDir>/public/js'],
};