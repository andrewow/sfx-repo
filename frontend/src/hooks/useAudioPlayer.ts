import { useCallback, useEffect, useRef, useState } from "react";
import { getAudioUrl } from "../api/sounds";

interface AudioPlayerState {
  currentSoundId: string | null;
  isPlaying: boolean;
  currentTime: number;
  duration: number;
}

let globalAudio: HTMLAudioElement | null = null;

export function useAudioPlayer() {
  const [state, setState] = useState<AudioPlayerState>({
    currentSoundId: null,
    isPlaying: false,
    currentTime: 0,
    duration: 0,
  });

  const stateRef = useRef(state);
  stateRef.current = state;

  useEffect(() => {
    if (!globalAudio) {
      globalAudio = new Audio();
    }

    const audio = globalAudio;

    const onTimeUpdate = () =>
      setState((s) => ({ ...s, currentTime: audio.currentTime }));
    const onDurationChange = () =>
      setState((s) => ({ ...s, duration: audio.duration || 0 }));
    const onEnded = () =>
      setState((s) => ({ ...s, isPlaying: false, currentTime: 0 }));
    const onPlay = () => setState((s) => ({ ...s, isPlaying: true }));
    const onPause = () => setState((s) => ({ ...s, isPlaying: false }));

    audio.addEventListener("timeupdate", onTimeUpdate);
    audio.addEventListener("durationchange", onDurationChange);
    audio.addEventListener("ended", onEnded);
    audio.addEventListener("play", onPlay);
    audio.addEventListener("pause", onPause);

    return () => {
      audio.removeEventListener("timeupdate", onTimeUpdate);
      audio.removeEventListener("durationchange", onDurationChange);
      audio.removeEventListener("ended", onEnded);
      audio.removeEventListener("play", onPlay);
      audio.removeEventListener("pause", onPause);
    };
  }, []);

  const play = useCallback((soundId: string) => {
    const audio = globalAudio!;
    if (stateRef.current.currentSoundId === soundId && !stateRef.current.isPlaying) {
      audio.play();
      return;
    }
    if (stateRef.current.currentSoundId !== soundId) {
      audio.src = getAudioUrl(soundId);
      setState((s) => ({ ...s, currentSoundId: soundId, currentTime: 0, duration: 0 }));
    }
    audio.play();
  }, []);

  const pause = useCallback(() => {
    globalAudio?.pause();
  }, []);

  const toggle = useCallback((soundId: string) => {
    if (stateRef.current.currentSoundId === soundId && stateRef.current.isPlaying) {
      pause();
    } else {
      play(soundId);
    }
  }, [play, pause]);

  const seek = useCallback((time: number) => {
    if (globalAudio) {
      globalAudio.currentTime = time;
    }
  }, []);

  return { ...state, play, pause, toggle, seek };
}
