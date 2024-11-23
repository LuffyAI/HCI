"use client";


import { useState, useEffect, useRef} from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ArrowUp, Delete, Keyboard, Lightbulb, Undo2 } from "lucide-react";

const BASE_URL = "http://localhost:8000";

const getSuggestions = async (text: string, isWordCompletion: boolean): Promise<string[]> => {
  const endpoint = isWordCompletion ? "/suggest_word_completion" : "/suggest_next_word";
  try {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await response.json();
    return data.suggestions;
  } catch (error) {
    console.error("Error fetching suggestions:", error);
    return [];
  }
};

const sendMessageAPI = async (sender: string, text: string): Promise<void> => {
  try {
    await fetch(`${BASE_URL}/send_message/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sender, text }),
    });
  } catch (error) {
    console.error("Error sending message:", error);
  }
};

const getOpenAISuggestions = async (data: any, endpoint:any): Promise<string[]> => {
  try {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const result = await response.json();
    console.log("OpenAI Sggestions received:", result);
    return result.suggestions;
  } catch (error) {
    console.error("Error fetching lightbulb suggestions:", error);
    return [];
  }
};


const getContextData = async (endpoint: any): Promise<string[]> => {
  try {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: "GET", // Change method to GET
      headers: { "Content-Type": "application/json" },
    });
    const result = await response.json();
    console.log("OpenAI Suggestions received:", result);
    return result.contexts; // Assuming the API returns a 'contexts' key
  } catch (error) {
    console.error("Error fetching lightbulb suggestions:", error);
    return [];
  }
};


type Message = {
  text: string;
  sender: "user" | "other";
};

export default function Component() {
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isUpperCase, setIsUpperCase] = useState(false);
  const [isSpecialChar, setIsSpecialChar] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [selectedContext, setSelectedContext] = useState<string | null>(null);

  // Light Bulb Button States
  const [useLightbulbSuggestions, setUseLightbulbSuggestions] = useState(false);
  const [isLightbulbActive, setIsLightbulbActive] = useState(false);

  //Checkmark button states
  const [useCheckMarkSuggestion, setUseCheckMarkSuggestions] = useState(false);
  const [isCheckMarkActive, setisCheckMarkActive] = useState(false);

//Checkmark button states
const [useCxtMode, setCxtMode] = useState(false);
const [isCxtModeActive, setCxtModeActive] = useState(false);


  const [lastIndex, setLastIndex] = useState(0);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const updateDeviceType = () => {
      setIsMobile(window.innerWidth <= 768); // Assuming mobile if width <= 768px
    };

    updateDeviceType(); // Initial check
    window.addEventListener("resize", updateDeviceType);
    return () => window.removeEventListener("resize", updateDeviceType);
  }, []);



  // State to manage intervals for key holding
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  
  // Start repeating the keypress
  const handleKeyPressHold = (key: string) => {
    // Exceptions for certain keys
    if (["shift", "send", "✔", "lightbulb"].includes(key.toLowerCase())) {
      handleKeyPress(key);
      return;
    }
  
    // Trigger initial keypress immediately
    handleKeyPress(key);
  
    // Set interval to repeat the keypress
    intervalRef.current = setInterval(() => {
      handleKeyPress(key);
    }, 150); // Repeat every 150ms
  };
  
  // Stop repeating the keypress
  const handleKeyRelease = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
  };
 
  
  useEffect(() => {
    let polling = true; // Flag to control polling
    let currentIndex = lastIndex; // Use a local variable for last index tracking
  
    const pollMessages = async () => {
      try {
        const response = await fetch(`${BASE_URL}/get_messages/?start_index=${currentIndex}`);
        const newMessages = await response.json();
  
        if (newMessages.length > 0) {
          setMessages((prevMessages) => {
            // Ensure no duplicates by filtering new messages
            const uniqueMessages = newMessages.filter(
              (newMsg) => !prevMessages.some((msg) => msg.text === newMsg.text && msg.sender === newMsg.sender)
            );
            return [...prevMessages, ...uniqueMessages];
          });
  
          currentIndex += newMessages.length; // Update local index
          setLastIndex(currentIndex); // Sync with state
        }
      } catch (error) {
        console.error("Error polling messages:", error);
      }
    };
  
    const interval = setInterval(() => {
      if (polling) pollMessages();
    }, 1000);
  
    return () => {
      polling = false; // Stop polling
      clearInterval(interval);
    };
  }, []); // Remove `lastIndex`

  // Fetch suggestions (default or lightbulb)
  useEffect(() => {
    if (input && !useLightbulbSuggestions) {
      const isWordCompletion = input[input.length - 1] !== " ";
      const contextText = isWordCompletion
        ? input.split(" ").slice(-15).join(" ")
        : input.trim();
      getSuggestions(contextText, isWordCompletion).then(setSuggestions);
    } else if (!input && !useLightbulbSuggestions) {
      setSuggestions([]);
    }
  }, [input, useLightbulbSuggestions]);





  
  const handleCheckMarkClick = async () => {
    console.log("Checkmark clicked. Current Checkmark mode:", useCheckMarkSuggestion);
  
    if (useCheckMarkSuggestion) {
      // Turn off lightbulb suggestions and enable default suggestions
      setUseCheckMarkSuggestions(false);
      setSuggestions([]); // Clear suggestionsa
      setisCheckMarkActive(false);
      console.log("Checkmark mode deactivated. Default suggestions re-enabled.");
      return;
    }

     // Prepare data for API
     const previousContext = messages
     .map((message) => `${message.sender === "user" ? "You" : "Other"}: ${message.text}`)
     .join(" ");
 
   const data = {
     previous_context: previousContext,
     user_current_input: input,
     context_mode: "",
     button_press: "Yellow",
     suggestions: [],
   };
 
   console.log("Sending data to Checkmark API:", data);
 
   try {
     // Call lightbulb API and wait for response
     const newSuggestions = await getOpenAISuggestions(data,"/checkmark_click/");
     
 
     if (newSuggestions && newSuggestions.length > 0) {
       console.log("Lightbulb suggestions received:", newSuggestions);
       setUseCheckMarkSuggestions(true); // Enable lightbulb mode
       setSuggestions(newSuggestions);  // Update suggestions in UI
     } else {
       console.warn("Lightbulb API returned an empty or invalid response:", newSuggestions);
       setSuggestions([]); // Clear suggestions if API returns no results
       setisCheckMarkActive(false);
     }
   } catch (error) {
     console.error("Error fetching lightbulb suggestionchecks:", error);
     setSuggestions([]); // Clear suggestions on error
     setisCheckMarkActive(false);
   }
 };

 const setContextMode = async (selectedContext) => {
  try {
    const response = await fetch(`${BASE_URL}/set_context_mode/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: selectedContext }),
    });

    if (!response.ok) {
      console.error("Failed to set context mode:", response.statusText);
      return null;
    }

    const result = await response.json();
    console.log("Context mode updated successfully:", result);
    setCxtMode(false);
    return result.new_context_mode; // Return the updated context mode
  } catch (error) {
    console.error("Error setting context mode:", error);
    return null;
  }
};


 const handleContextClick = async () => {

  console.log("Context Mode clicked. Current Mode:", useCxtMode);
  
  if (useCxtMode) {
    setCxtMode(false);
    setSuggestions([]); // Clear suggestionsa
    setCxtModeActive(false);
    console.log("Checkmark mode deactivated. Default suggestions re-enabled.");
    return;
  }

 try {
   // Call lightbulb API and wait for response
   const newSuggestions = await getContextData("/get_context_mode/");
   

   if (newSuggestions && newSuggestions.length > 0) {
     console.log("Context modes received:", newSuggestions);
     setCxtMode(true); // Enable lightbulb mode
     setSuggestions(newSuggestions);  // Update suggestions in UI
   } else {
     console.warn("Lightbulb API returned an empty or invalid response:", newSuggestions);
     setSuggestions([]); // Clear suggestions if API returns no results
     setCxtModeActive(false);
   }
 } catch (error) {
   console.error("Error fetching Context Modes:", error);
   setSuggestions([]); // Clear suggestions on error
   setCxtModeActive(false);
 }

 };
  


  const handleLightbulbClick = async () => {
    console.log("Lightbulb clicked. Current lightbulb mode:", useLightbulbSuggestions);
  
    if (useLightbulbSuggestions) {
      // Turn off lightbulb suggestions and enable default suggestions
      setUseLightbulbSuggestions(false);
      setSuggestions([]); // Clear suggestionsa
      setIsLightbulbActive(false);
      console.log("Lightbulb mode deactivated. Default suggestions re-enabled.");
      return;
    }
  
    // Prepare data for API
    const previousContext = messages
      .map((message) => `${message.sender === "user" ? "You" : "Other"}: ${message.text}`)
      .join(" ");
  
    const data = {
      previous_context: previousContext,
      user_current_input: input,
      context_mode: "",
      button_press: "Yellow",
      suggestions: [],
    };
  
    console.log("Sending data to lightbulb API:", data);
  
    try {
      // Call lightbulb API and wait for response
      const newSuggestions = await getOpenAISuggestions(data,"/lightbulb_click/");
      
  
      if (newSuggestions && newSuggestions.length > 0) {
        console.log("Lightbulb suggestions received:", newSuggestions);
        setUseLightbulbSuggestions(true); // Enable lightbulb mode
        setSuggestions(newSuggestions);  // Update suggestions in UI
      } else {
        console.warn("Lightbulb API returned an empty or invalid response:", newSuggestions);
        setSuggestions([]); // Clear suggestions if API returns no results
        setIsLightbulbActive(false);
      }
    } catch (error) {
      console.error("Error fetching lightbulb suggestions:", error);
      setSuggestions([]); // Clear suggestions on error
      setIsLightbulbActive(false);
    }
  };


  const handleKeyPress = (key: string) => {
    const cursorPosition = inputRef.current?.selectionStart || 0;
  
    if (key === "backspace") {
      if (cursorPosition > 0) {
        const newInput =
          input.slice(0, cursorPosition - 1) + input.slice(cursorPosition);
        setInput(newInput);
  
        // Restore the cursor position
        setTimeout(() => {
          inputRef.current?.setSelectionRange(cursorPosition - 1, cursorPosition - 1);
        });
      }
    } else if (key === "undo") {
      setInput(input.slice(0, -1));
    } else if (key === "space") {
      const newInput =
        input.slice(0, cursorPosition) + " " + input.slice(cursorPosition);
      setInput(newInput);
  
      // Restore the cursor position
      setTimeout(() => {
        inputRef.current?.setSelectionRange(cursorPosition + 1, cursorPosition + 1);
      });
    } else if (key === "send") {
      if (input.trim()) {
        sendMessageAPI("user", input.trim());
        setInput("");
      }
    } else if (key === "✔") {
      handleCheckMarkClick();
    } else if (key === "👥") {
      handleContextClick();


    }   

    else {
      const newInput =
        input.slice(0, cursorPosition) +
        (isUpperCase ? key.toUpperCase() : key) +
        input.slice(cursorPosition);
      setInput(newInput);
  
      // Restore the cursor position
      setTimeout(() => {
        inputRef.current?.setSelectionRange(cursorPosition + 1, cursorPosition + 1);
      });
    }
  };

  useEffect(() => {
    if (useCxtMode) {
      // Fetch context-specific suggestions
      getContextData("/get_context_mode/").then(setSuggestions);
    } else if (input) {
      // Fetch default suggestions if context mode is inactive
      const isWordCompletion = input[input.length - 1] !== " ";
      const contextText = isWordCompletion
        ? input.split(" ").slice(-15).join(" ")
        : input.trim();
      getSuggestions(contextText, isWordCompletion).then(setSuggestions);
    } else {
      setSuggestions([]); // Clear suggestions if input is empty
    }
  }, [input, useCxtMode]);

  const numberKeys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"];
  const letterKeys = [
    ["✔","q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
    ["a", "s", "d", "f", "g", "h", "j", "k", "l"],
    ["shift", "z", "x", "c", "v", "b", "n", "m", "backspace"],
    ["123",":", "space", ".", "👥","↩ "],
  ];
  const specialKeys = [
    ["+", "×", "÷", "=", "/", "_", "<", ">", "[", "]"],
    ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")"],
    ["-", "'", "", ":", ";", ",", "?", "backspace"],
    ["abc", ":", "space", ".", "👥", "↩"],
  ];

  const keys = isSpecialChar ? specialKeys : letterKeys;

  
  return (
    <Card className="w-full max-w-lg mx-auto h-screen flex flex-col justify-between bg-white shadow-lg md:max-w-3xl">
      <div className="flex-grow h-1/2 overflow-y-auto p-4 bg-gray-100">
        {messages.map((message, index) => (
          <div key={index} className={`mb-2 flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}>
            <span
              className={`rounded-lg px-3 py-2 inline-block ${
                message.sender === "user" ? "bg-green-500 text-white" : "bg-blue-500 text-white"
              }`}
            >
              {message.text}
            </span>
          </div>
        ))}
      </div>

         {/* Input Section */}
         <div className="p-2 bg-gray-200 border-t border-gray-300">
             <div className="flex items-center bg-white rounded-md p-1 shadow-sm">
               {/* Input Field */}
               <textarea
                 type="text"
                 value={input}
                 onChange={(e) => setInput(e.target.value)}
                 ref={inputRef}
                 className="flex-grow p-2 rounded-l-md bg-white focus:outline-none text-sm resize-none max-h-24 overflow-y-auto"
                 placeholder="Type a message..."
                 autoFocus
               />
                {/* Send Button */}
               <button
                 onClick={() => {
                   if (input.trim()) {
                     sendMessageAPI("user", input.trim());
                     setInput("");
                   }
                 }}
                 className="ml-2 bg-blue-500 text-white p-2 rounded-md hover:bg-blue-600 focus:outline-none"
                 style={{ height: "100%" }}
               >
                 {/* Paper Plane Icon */}
                 <svg
                   xmlns="http://www.w3.org/2000/svg"
                   className="h-5 w-5"
                   fill="currentColor"
                   viewBox="0 0 24 24"
                 >
                   <path
                     fillRule="evenodd"
                     d="M2.707 12.293a1 1 0 01.083-1.32l.094-.083 17-9a1 1 0 011.32 1.497l-.094.083L7.413 11H20a1 1 0 01.993.883L21 12a1 1 0 01-.883.993L20 13H7.413l13.698 7.583a1 1 0 01-1.216 1.616l-.094-.055-17-9a1 1 0 01-.083-1.32l.094-.083-.094.083z"
                     clipRule="evenodd"
                   />
                 </svg>
               </button>
             </div>
           </div>


     {/* Suggestions Section */}
     <div className="flex gap-2 justify-around p-2 bg-gray-300 overflow-x-auto no-scrollbar">
  {useCxtMode
    ? suggestions.map((suggestion, index) => (
        <div
          key={index}
          className={`text-sm px-2 py-1 max-w-xs border rounded shadow-md overflow-x-auto whitespace-nowrap cursor-pointer ${
            index === 0 ? "bg-green-500 text-white" : "bg-white"
          }`}
          style={{ display: "inline-block" }}
          title={suggestion}
          onClick={async () => {
            console.log(`Setting context mode to: ${suggestion}`);
            const newContext = await setContextMode(suggestion);
            if (newContext) {
              console.log(`Context mode successfully updated to: ${newContext}`);
              setSuggestions([]); // Close the suggestion box
            } else {
              console.error("Failed to update context mode");
            }
          }}
        >
          {suggestion}
        </div>
      ))
    : suggestions.map((suggestion, index) => (
        <div
          key={index}
          className="text-sm px-2 py-1 max-w-xs bg-white border rounded shadow-md overflow-x-auto whitespace-nowrap cursor-pointer"
          style={{ display: "inline-block" }}
          title={suggestion}
          onClick={() => setInput(input + suggestion + " ")}
        >
          {suggestion}
        </div>
      ))}
</div>
            {/* Keyboard Section */}
      <div className="bg-gray-200 p-1">
        <div className="flex justify-between mb-1">
          <Button
            variant="secondary"
            className="flex-grow p-2 rounded-l-md bg-white focus:outline-none text-sm resize-none max-h-24 overflow-y-auto"
            onClick={handleLightbulbClick}
          >
            <Lightbulb className="w-4 h-4 md:w-5 md:h-5" />
          </Button>
          {numberKeys.map((key) => (
            <Button
              key={key}
              variant="secondary"
              className="flex-grow p-2 rounded-l-md bg-white focus:outline-none text-sm resize-none max-h-24 overflow-y-auto"
              onClick={() => handleKeyPress(key)}
            >
              {key}
            </Button>
          ))}
        </div>
        {keys.map((row, rowIndex) => (
          <div key={rowIndex} className="flex justify-center mb-1">
            {row.map((key, keyIndex) => (
              <Button
                key={keyIndex}
                variant="secondary"
                className={`m-0.5 ${
                  key === "space"
                    ? "flex-grow"
                    : key === "shift" || key === "backspace" || key === "undo"
                    ? "w-12 md:w-16"
                    : key === "123" || key === "send" || key === "abc"
                    ? "flex-grow p-2 rounded-l-md bg-white focus:outline-none text-sm resize-none max-h-24 overflow-y-auto"
                    : "flex-grow p-2 rounded-l-md bg-white focus:outline-none text-sm resize-none max-h-24 overflow-y-auto"
                } h-10 md:h-12 text-sm md:text-base font-medium`}
                onClick={() => {
                  if (key === "shift") {
                    setIsUpperCase(!isUpperCase);
                  } else if (key === "123") {
                    setIsSpecialChar(true);
                  } else if (key === "abc") {
                    setIsSpecialChar(false);
                  } else {
                    handleKeyPress(key);
                  }
                }}
              >
                {key === "backspace" ? (
                  <Delete className="w-4 h-4 md:w-5 md:h-5" />
                ) : key === "undo" ? (
                  <Undo2 className="w-4 h-4 md:w-5 md:h-5" />
                ) : key === "shift" ? (
                  <ArrowUp className="w-4 h-4 md:w-5 md:h-5" />
                ) : key === "123" || key === "abc" ? (
                  <Keyboard className="w-4 h-4 md:w-5 md:h-5" />
                ) : (
                  isUpperCase ? key.toUpperCase() : key
                )}
              </Button>
            ))}
          </div>
        ))}
      </div>
    </Card>
  );
}
