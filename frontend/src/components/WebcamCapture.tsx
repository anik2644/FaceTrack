"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Camera, RefreshCw, Upload } from "lucide-react";
import { Button } from "@/components/ui";

interface Props {
  onCapture: (dataUrl: string) => void;
  captured: string | null;
}

/** Reusable webcam capture widget with an upload fallback. */
export default function WebcamCapture({ onCapture, captured }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  const startCamera = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setReady(true);
    } catch {
      setError("Unable to access webcam. Use the upload option instead.");
    }
  }, []);

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setReady(false);
  }, []);

  useEffect(() => {
    startCamera();
    return stopCamera;
  }, [startCamera, stopCamera]);

  const capture = () => {
    const video = videoRef.current;
    if (!video) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d")?.drawImage(video, 0, 0);
    onCapture(canvas.toDataURL("image/jpeg", 0.9));
  };

  const onUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => onCapture(reader.result as string);
    reader.readAsDataURL(file);
  };

  return (
    <div className="space-y-3">
      <div className="relative overflow-hidden rounded-xl bg-slate-900 aspect-video">
        {captured ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={captured} alt="Captured" className="h-full w-full object-cover" />
        ) : (
          <video ref={videoRef} className="h-full w-full object-cover" muted playsInline />
        )}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center p-4 text-center text-sm text-amber-300">
            {error}
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        {captured ? (
          <Button variant="secondary" onClick={() => onCapture("")} type="button">
            <RefreshCw className="h-4 w-4" /> Retake
          </Button>
        ) : (
          <Button onClick={capture} disabled={!ready} type="button">
            <Camera className="h-4 w-4" /> Capture
          </Button>
        )}
        <label className="btn-secondary cursor-pointer">
          <Upload className="h-4 w-4" /> Upload
          <input type="file" accept="image/*" className="hidden" onChange={onUpload} />
        </label>
      </div>
    </div>
  );
}
