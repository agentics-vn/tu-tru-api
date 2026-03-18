"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";

export interface Profile {
  name?: string;
  birthDate: string; // YYYY-MM-DD
  birthHour: string; // "ty"|"suu"|...|"hoi"|"unknown"
  gender: "nam" | "nu";
}

interface ProfileContextType {
  profile: Profile | null;
  setProfile: (p: Profile) => void;
  clearProfile: () => void;
  isLoaded: boolean;
}

const ProfileContext = createContext<ProfileContextType>({
  profile: null,
  setProfile: () => {},
  clearProfile: () => {},
  isLoaded: false,
});

const STORAGE_KEY = "tutru_profile";

export function ProfileProvider({ children }: { children: ReactNode }) {
  const [profile, setProfileState] = useState<Profile | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) setProfileState(JSON.parse(stored));
    } catch {
      /* ignore */
    }
    setIsLoaded(true);
  }, []);

  const setProfile = (p: Profile) => {
    setProfileState(p);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(p));
  };

  const clearProfile = () => {
    setProfileState(null);
    localStorage.removeItem(STORAGE_KEY);
  };

  return (
    <ProfileContext.Provider
      value={{ profile, setProfile, clearProfile, isLoaded }}
    >
      {children}
    </ProfileContext.Provider>
  );
}

export function useProfile() {
  return useContext(ProfileContext);
}
