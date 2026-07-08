const FaceBoxOverlay = ({ faces }) => {
  if (!faces || faces.length === 0) return null;

  return (
    <>
      {faces.map((f, index) => {
        const [x1, y1, x2, y2] = f.box;

        return (
          <div
            key={index}
            className="absolute border-2 border-green-400 rounded-xl"
            style={{
              left: x1,
              top: y1,
              width: x2 - x1,
              height: y2 - y1,
              boxShadow: "0 0 20px rgba(0,255,0,0.5)",
            }}
          />
        );
      })}
    </>
  );
};

export default FaceBoxOverlay;
