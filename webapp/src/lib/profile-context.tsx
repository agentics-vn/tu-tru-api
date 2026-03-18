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

function isValidProfile(obj: unknown): obj is Profile {
  if (typeof obj !== "object" || obj === null) return false;
  const p = obj as Record<string, unknown>;
  return (
    typeof p.birthDate === "string" &&
    typeof p.birthHour === "string" &&
    (p.gender === "nam" || p.gender === "nu")
  );
}

export function ProfileProvider({ children }: { children: ReactNode }) {
  const [profile, setProfileState] = useState<Profile | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed: unknown = JSON.parse(stored);
        if (isValidProfile(parsed)) {
          setProfileState(parsed);
        } else {
          localStorage.removeItem(STORAGE_KEY);
        }
      }
    } catch {
      localStorage.removeItem(STORAGE_KEY);
    }
    setIsLoaded(true);
  }, []);

  const setProfile = (p: Profile) => {
    setProfileState(p);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(p));
    } catch {
      /* storage full or disabled — profile still works in memory */
    }
  };

  const clearProfile = () => {
    setProfileState(null);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* ignore */
    }
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
