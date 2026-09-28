// We will dynamically import pdfjs-dist to avoid SSR canvas resolution errors

export interface AttachedFile {
  id: string;
  file: File;
  type: 'image' | 'pdf';
  base64Data: string; // The base64 representation to send to the AI
  previewUrl: string; // The URL to show in the UI thumbnail
}

/**
 * Converts a standard File object into a Base64 string.
 */
export const fileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = (error) => reject(error);
  });
};

/**
 * Parses a PDF file and converts its first page to a Base64 image.
 */
export const convertPdfToImage = async (file: File): Promise<string> => {
  try {
    const pdfjsLib = await import('pdfjs-dist');
    if (typeof window !== 'undefined') {
      pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;
    }

    const arrayBuffer = await file.arrayBuffer();
    const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer });
    const pdf = await loadingTask.promise;
    
    const pageNumber = 1;
    const page = await pdf.getPage(pageNumber);
    
    const scale = 2.0; 
    const viewport = page.getViewport({ scale });
    
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    
    if (!context) {
      throw new Error("Could not create canvas context");
    }
    
    canvas.height = viewport.height;
    canvas.width = viewport.width;
    
    const renderContext = {
      canvasContext: context,
      viewport: viewport
    };
    
    await page.render(renderContext).promise;
    
    return canvas.toDataURL('image/jpeg', 0.9);
  } catch (error) {
    console.error("Error converting PDF to image:", error);
    throw new Error("Failed to process PDF file.");
  }
};

/**
 * Process an array of uploaded files and returns AttachedFile objects
 */
export const processUploadedFiles = async (files: FileList | null): Promise<AttachedFile[]> => {
  if (!files) return [];
  
  const processedFiles: AttachedFile[] = [];
  
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    const id = Math.random().toString(36).substring(7);
    
    if (file.type.startsWith('image/')) {
      const base64Data = await fileToBase64(file);
      processedFiles.push({
        id,
        file,
        type: 'image',
        base64Data,
        previewUrl: base64Data 
      });
    } else if (file.type === 'application/pdf') {
      const base64Data = await convertPdfToImage(file);
      processedFiles.push({
        id,
        file,
        type: 'pdf',
        base64Data,
        previewUrl: base64Data 
      });
    } else {
      console.warn(`Unsupported file type: ${file.type}`);
    }
  }
  
  return processedFiles;
};
