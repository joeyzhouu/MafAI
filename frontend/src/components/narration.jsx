import { useEffect, useState, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { io } from "socket.io-client";

export default function Narration() {
  const location = useLocation();
  const navigate = useNavigate();

  const { gameId, playerId, name, story: initialStory } = location.state || {};

  const [story, setStory] = useState(initialStory || "");
  const [storyType, setStoryType] = useState("story");

  const [displayedText, setDisplayedText] = useState("");
  const [allGeneratedText, setAllGeneratedText] = useState("");
  const [sentences, setSentences] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isTyping, setIsTyping] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [animationDirection, setAnimationDirection] = useState(1);
  const [isUserScrolling, setIsUserScrolling] = useState(false);
  const [showCompleteText, setShowCompleteText] = useState(false);
  const [hasContinued, setHasContinued] = useState(false);
  const [socket, setSocket] = useState(null);

  const textBoxRef = useRef(null);

  const totalFrames = 16;
  const frameWidth = 64;

  const handleScroll = () => {
    if (textBoxRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = textBoxRef.current;
      setIsUserScrolling(scrollTop + clientHeight < scrollHeight - 5);
    }
  };

  // Socket connection
  useEffect(() => {
    if (!gameId || !playerId) {
      navigate("/");
      return;
    }

    const s = io("http://localhost:5001");
    setSocket(s);

    s.emit("join", { game_id: gameId, player_id: playerId });

    s.on("game_started", (data) => {
      if (data.background_story) {
        setStory(data.background_story);
        setStoryType("background");
      }
    });

    s.on("day_started", (data) => {
      if (data.story) {
        setStory(data.story);
        setStoryType("day");
      }
    });

    s.on("player_continue_update", (data) => {
      console.log("Player continue update:", data);
      // Optionally show a list of players who have continued
    });

    s.on("all_players_continued", () => {
      // Navigate to next page once all players pressed continue
      if (storyType === "background") {
        navigate("/night-phase", { state: { gameId, playerId, name } });
      } else if (storyType === "day") {
        navigate("/discussion-phase", { state: { gameId, playerId, name } });
      } else {
        navigate("/");
      }
    });

    return () => s.disconnect();
  }, [gameId, playerId, navigate, storyType, name]);

  // Split story into sentences
  useEffect(() => {
    if (story) {
      const parts = story
        .split(".")
        .map((s) => s.trim())
        .filter((s) => s.length);
      setSentences(parts);
      setCurrentIndex(0);
      setDisplayedText("");
      setAllGeneratedText("");
      setShowCompleteText(false);
      setIsTyping(false);
      setHasContinued(false);
    }
  }, [story]);

  useEffect(() => {
    if (!isUserScrolling && textBoxRef.current) {
      textBoxRef.current.scrollTop = textBoxRef.current.scrollHeight;
    }
  }, [allGeneratedText, isUserScrolling]);

  // Sprite animation effect
  useEffect(() => {
    if (!isTyping) {
      setCurrentFrame(0);
      setAnimationDirection(1);
      return;
    }

    const frameInterval = setInterval(() => {
      setCurrentFrame((prevFrame) => {
        let nextFrame = prevFrame + animationDirection;
        if (nextFrame >= totalFrames - 1) {
          setAnimationDirection(-1);
          return totalFrames - 1;
        } else if (nextFrame <= 0) {
          setAnimationDirection(1);
          return 0;
        }
        return nextFrame;
      });
    }, 350);

    return () => clearInterval(frameInterval);
  }, [isTyping, animationDirection]);

  // Typing effect
  useEffect(() => {
    if (sentences.length === 0 || currentIndex >= sentences.length) {
      setIsTyping(false);
      setShowCompleteText(true);
      return;
    }

    const sentence = sentences[currentIndex];
    let i = 0;
    setDisplayedText("");
    setIsTyping(true);

    const interval = setInterval(() => {
      if (i < sentence.length) {
        const char = sentence[i];
        if (char !== undefined) {
          setDisplayedText((prev) => prev + char);
          setAllGeneratedText((prev) => prev + char);
        }
        i++;
      } else {
        clearInterval(interval);
        setIsTyping(false);
        if (!sentence.trim().endsWith(".")) {
          setAllGeneratedText((prev) => prev + ". ");
        } else {
          setAllGeneratedText((prev) => prev + " ");
        }
        setTimeout(() => setCurrentIndex((idx) => idx + 1), 1000);
      }
    }, 50);

    return () => clearInterval(interval);
  }, [currentIndex, sentences]);

  // Continue button handler
  const handleContinue = () => {
    if (socket && !hasContinued) {
      socket.emit("player_continue", { game_id: gameId, player_id: playerId });
      setHasContinued(true);
    }
  };

  if (!story) {
    return (
      <div className="flex flex-col h-screen items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800 text-white">
        <div className="text-2xl font-medium mb-4">Waiting for story...</div>
        <div className="text-lg text-gray-400">Game: {gameId}</div>
        <div className="text-lg text-gray-400">Player: {name}</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800 text-white">
      <div className="absolute top-6 left-6 text-white text-lg">
        Game: {gameId} | Player: {name}
      </div>
      <div className="absolute top-6 right-6 text-white text-lg capitalize">
        {storyType} Story
      </div>

      <div className="relative mb-8">
        <div
          className="w-16 h-16 overflow-hidden"
          style={{
            backgroundImage: `url(/assets/talking-guy.png)`,
            backgroundSize: `${totalFrames * 100}% 100%`,
            backgroundPosition: `-${currentFrame * frameWidth}px 0px`,
            backgroundRepeat: "no-repeat",
            imageRendering: "pixelated",
            imageRendering: "-moz-crisp-edges",
            imageRendering: "crisp-edges",
          }}
        />
      </div>

      <div className="w-3/4 max-w-2xl text-center">
        <div
          ref={textBoxRef}
          onScroll={handleScroll}
          className="text-xl font-medium p-6 rounded-lg bg-black bg-opacity-30 backdrop-blur-sm border border-white border-opacity-20 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-transparent"
          style={{ height: "12rem", minHeight: "12rem" }}
        >
          <div className="text-left">{allGeneratedText}</div>
        </div>
      </div>

      <button
        onClick={handleContinue}
        className={`mt-12 py-2 px-6 rounded-lg font-semibold text-lg transition-all duration-200 hover:scale-105 active:scale-95 ${
          hasContinued
            ? "bg-gray-600 hover:bg-gray-700 text-gray-300 cursor-default"
            : "bg-green-500 hover:bg-green-600 text-white"
        }`}
        disabled={hasContinued}
      >
        {hasContinued ? "Waiting for others..." : "Continue"}
      </button>
    </div>
  );
}
