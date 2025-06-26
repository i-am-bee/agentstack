/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { PauseFilled, PlayFilledAlt } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import clsx from 'clsx';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useIntersectionObserver } from 'usehooks-ts';

import classes from './ShowcaseVideo.module.scss';

interface Props {
  src: string;
  poster: string;
  className?: string;
}

export function ShowcaseVideo({ src, poster, className }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [played, setPlayed] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);

  const { isIntersecting, ref } = useIntersectionObserver({
    threshold: 0.75,
  });

  const togglePlay = useCallback(() => {
    const video = videoRef.current;

    if (!video) {
      return;
    }

    if (video.paused || video.ended) {
      video.play();
    } else {
      video.pause();
    }
  }, []);

  useEffect(() => {
    const video = videoRef.current;

    if (!video || played) {
      return;
    }

    if (isIntersecting && video.paused) {
      video.play();
    } else if (!video.paused) {
      video.pause();
    }
  }, [isIntersecting, played]);

  useEffect(() => {
    const video = videoRef.current;

    if (!video) {
      return;
    }

    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleEnded = () => {
      setIsPlaying(false);
      setPlayed(true);
    };

    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);
    video.addEventListener('ended', handleEnded);

    return () => {
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
      video.removeEventListener('ended', handleEnded);
    };
  }, []);

  return (
    <div className={clsx(classes.root, className)} ref={ref}>
      <IconButton
        size="md"
        kind="ghost"
        label={isPlaying ? 'Pause' : 'Play'}
        onClick={togglePlay}
        wrapperClasses={classes.button}
      >
        {isPlaying ? <PauseFilled /> : <PlayFilledAlt />}
      </IconButton>

      <video ref={videoRef} src={src} poster={poster} muted />
    </div>
  );
}
