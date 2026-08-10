import { motion, AnimatePresence } from 'motion/react';
import React from 'react';
export interface LiveDataPayload {
  crop: string;
  district: string;
  price: string;
  temperature: number;
  date: string;
}

interface LiveDataCardProps {
  data: LiveDataPayload | null;
}

export function LiveDataCard({ data }: LiveDataCardProps) {
  return (
    <AnimatePresence>
      {data && (
        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 20, scale: 0.95 }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
          className="absolute top-24 left-4 z-[70] w-80 md:top-32 md:left-12"
        >
          <div className="overflow-hidden rounded-xl border border-white/10 bg-white/10 backdrop-blur-md shadow-2xl dark:bg-black/40">
            <div className="bg-primary/20 px-4 py-2 text-xs font-bold uppercase tracking-wider text-primary">
              Live Data / थेट माहिती
            </div>
            <div className="p-5">
              <div className="mb-4">
                <div className="text-muted-foreground text-xs font-medium uppercase tracking-wider">
                  Location / ठिकाण
                </div>
                <div className="text-foreground text-xl font-semibold">
                  {data.district}
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-muted-foreground text-xs font-medium uppercase tracking-wider">
                    Crop / पीक
                  </div>
                  <div className="text-foreground text-lg font-medium">
                    {data.crop}
                  </div>
                  <div className="text-foreground mt-1 text-2xl font-bold text-green-500">
                    ₹{data.price}
                    <span className="text-muted-foreground ml-1 text-sm font-normal">/Q</span>
                  </div>
                </div>
                
                <div>
                  <div className="text-muted-foreground text-xs font-medium uppercase tracking-wider">
                    Weather / हवामान
                  </div>
                  <div className="mt-1 flex items-center gap-2">
                    <span className="text-3xl">🌤️</span>
                    <div className="text-foreground text-2xl font-bold">
                      {data.temperature}°C
                    </div>
                  </div>
                </div>
              </div>

              <div className="text-muted-foreground mt-4 border-t border-white/10 pt-3 text-right text-xs">
                As of {data.date}
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
