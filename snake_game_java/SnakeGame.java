import javax.swing.AbstractAction;
import javax.swing.ActionMap;
import javax.swing.InputMap;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.KeyStroke;
import javax.swing.SwingUtilities;
import javax.swing.Timer;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.FontMetrics;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.event.ActionEvent;
import java.awt.event.KeyEvent;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;
import java.util.Random;

/**
 * 基于 Java Swing 的贪吃蛇小游戏，不依赖任何第三方库。
 * <p>
 * 操作方式：
 * <ul>
 *   <li>方向键 / WASD：控制移动，在开始界面按下即开局</li>
 *   <li>空格：开始界面开局，运行中暂停 / 继续</li>
 *   <li>回车：游戏结束后重新开始</li>
 *   <li>鼠标点击：开始 / 暂停 / 重开</li>
 * </ul>
 * 已调用 {@code enableInputMethods(false)} 禁用输入法，
 * 因此中文输入法下 WASD 依然可用，无需手动切到英文。
 */
public class SnakeGame extends JPanel {

    /** 每个格子的像素大小 */
    private static final int CELL_SIZE = 25;
    /** 横向格子数 */
    private static final int COLS = 28;
    /** 纵向格子数 */
    private static final int ROWS = 22;

    private static final int WIDTH = COLS * CELL_SIZE;
    private static final int HEIGHT = ROWS * CELL_SIZE;

    /** 初始移动间隔（毫秒），越小越快 */
    private static final int INIT_DELAY = 140;
    /** 最快速度上限 */
    private static final int MIN_DELAY = 60;
    /** 每吃一个食物加快的毫秒数 */
    private static final int SPEED_UP_STEP = 4;

    /** 方向向量：上、下、左、右 */
    private static final int[] DX = {0, 0, -1, 1};
    private static final int[] DY = {-1, 1, 0, 0};
    private static final int UP = 0, DOWN = 1, LEFT = 2, RIGHT = 3;

    private enum State {READY, RUNNING, PAUSED, OVER}

    /** 蛇身，队首为蛇头 */
    private final Deque<Integer> snake = new ArrayDeque<>();
    /** 待生效的转向队列，避免一帧内连续转向导致自撞 */
    private final List<Integer> pendingDirs = new ArrayList<>(3);

    private final Random random = new Random();
    private final Timer timer;

    private State state = State.READY;
    private int direction = RIGHT;
    private int foodX;
    private int foodY;
    private int score;
    private int highScore;

    public SnakeGame() {
        setPreferredSize(new Dimension(WIDTH, HEIGHT));
        setBackground(new Color(30, 32, 40));
        setFocusable(true);
        // 游戏面板不需要文本输入，必须禁用输入法。
        // 否则在中文输入法下，W/A/S/D 会被 IME 截去做拼音组词，
        // 按键事件根本不会送到 Java 窗口，表现为“按了 WASD 不能转向”（方向键不受影响）。
        enableInputMethods(false);
        bindKeys();
        bindMouse();

        timer = new Timer(INIT_DELAY, this::onTick);
        resetGame();
    }

    /**
     * 组件加入窗口时主动抢焦点。
     * <p>
     * 不抢焦点时窗口虽然可见，但键盘事件可能被其他组件或 IDE 控制台接走，
     * 表现为“按了方向键没反应”。
     */
    @Override
    public void addNotify() {
        super.addNotify();
        requestFocusInWindow();
    }

    /** 鼠标点击也能开始 / 重开 / 暂停，并在点击后把焦点拿回来 */
    private void bindMouse() {
        addMouseListener(new MouseAdapter() {
            @Override
            public void mousePressed(MouseEvent e) {
                requestFocusInWindow();
                switch (state) {
                    case READY -> startGame();
                    case OVER -> {
                        resetGame();
                        startGame();
                    }
                    default -> togglePause();
                }
            }
        });
    }

    /** 绑定键盘动作，使用 InputMap/ActionMap 保证焦点在本面板时生效 */
    private void bindKeys() {
        InputMap im = getInputMap(WHEN_IN_FOCUSED_WINDOW);
        ActionMap am = getActionMap();

        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_UP, 0), "up");
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_W, 0), "up");
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_DOWN, 0), "down");
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_S, 0), "down");
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_LEFT, 0), "left");
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_A, 0), "left");
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_RIGHT, 0), "right");
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_D, 0), "right");
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_SPACE, 0), "pause");
        im.put(KeyStroke.getKeyStroke(KeyEvent.VK_ENTER, 0), "restart");

        am.put("up", new AbstractAction() {
            @Override
            public void actionPerformed(ActionEvent e) {
                changeDirection(UP);
            }
        });
        am.put("down", new AbstractAction() {
            @Override
            public void actionPerformed(ActionEvent e) {
                changeDirection(DOWN);
            }
        });
        am.put("left", new AbstractAction() {
            @Override
            public void actionPerformed(ActionEvent e) {
                changeDirection(LEFT);
            }
        });
        am.put("right", new AbstractAction() {
            @Override
            public void actionPerformed(ActionEvent e) {
                changeDirection(RIGHT);
            }
        });
        am.put("pause", new AbstractAction() {
            @Override
            public void actionPerformed(ActionEvent e) {
                togglePause();
            }
        });
        am.put("restart", new AbstractAction() {
            @Override
            public void actionPerformed(ActionEvent e) {
                if (state == State.OVER) {
                    resetGame();
                }
                startGame();
            }
        });
    }

    /** 初始化/重置一局游戏 */
    private void resetGame() {
        timer.stop();
        timer.setDelay(INIT_DELAY);

        snake.clear();
        pendingDirs.clear();
        direction = RIGHT;
        score = 0;
        state = State.READY;

        int startX = COLS / 2;
        int startY = ROWS / 2;
        // 初始长度 3 节，蛇头在最前
        snake.addFirst(cell(startX - 2, startY));
        snake.addFirst(cell(startX - 1, startY));
        snake.addFirst(cell(startX, startY));

        spawnFood();
        repaint();
    }

    /** 从“准备”状态进入运行状态；其余状态下调用无效果 */
    private void startGame() {
        if (state != State.READY) {
            return;
        }
        state = State.RUNNING;
        timer.start();
        repaint();
    }

    private void changeDirection(int newDir) {
        startGame();
        if (state != State.RUNNING) {
            return;
        }
        // 参照方向取队列末尾（即真正生效的方向），禁止 180 度掉头
        int base = pendingDirs.isEmpty() ? direction : pendingDirs.get(pendingDirs.size() - 1);
        if (newDir == base || isOpposite(newDir, base)) {
            return;
        }
        if (pendingDirs.size() < 3) {
            pendingDirs.add(newDir);
        }
    }

    private static boolean isOpposite(int a, int b) {
        return (a == UP && b == DOWN) || (a == DOWN && b == UP)
                || (a == LEFT && b == RIGHT) || (a == RIGHT && b == LEFT);
    }

    private void togglePause() {
        // 空格在开始界面应直接开局，而不是什么都不做
        if (state == State.READY) {
            startGame();
            return;
        }
        if (state == State.RUNNING) {
            state = State.PAUSED;
            timer.stop();
        } else if (state == State.PAUSED) {
            state = State.RUNNING;
            timer.start();
        }
        repaint();
    }

    /** 定时器回调：推进一格 */
    private void onTick(ActionEvent e) {
        if (state != State.RUNNING) {
            return;
        }
        if (!pendingDirs.isEmpty()) {
            direction = pendingDirs.remove(0);
        }

        int head = snake.peekFirst();
        int hx = xOf(head) + DX[direction];
        int hy = yOf(head) + DY[direction];

        // 撞墙
        if (hx < 0 || hx >= COLS || hy < 0 || hy >= ROWS) {
            gameOver();
            return;
        }

        boolean ate = (hx == foodX && hy == foodY);
        int newHead = cell(hx, hy);

        // 撞到自己：如果不吃食物，尾巴会先移走，所以最后一节可以忽略
        if (!ate && isSelfHitExcludingTail(newHead, snake.peekLast())) {
            gameOver();
            return;
        }

        snake.addFirst(newHead);
        if (ate) {
            score += 10;
            if (score > highScore) {
                highScore = score;
            }
            int newDelay = Math.max(MIN_DELAY, timer.getDelay() - SPEED_UP_STEP);
            timer.setDelay(newDelay);
            spawnFood();
        } else {
            snake.removeLast();
        }
        repaint();
    }

    /** 判断新蛇头是否撞到自己（排除即将移开的尾巴） */
    private boolean isSelfHitExcludingTail(int newHead, int tail) {
        for (int part : snake) {
            if (part == tail) {
                continue;
            }
            if (part == newHead) {
                return true;
            }
        }
        return false;
    }

    private void gameOver() {
        state = State.OVER;
        timer.stop();
        repaint();
    }

    /** 在空白格随机生成食物 */
    private void spawnFood() {
        int free = COLS * ROWS - snake.size();
        if (free <= 0) {
            gameOver();
            return;
        }
        int index = random.nextInt(free);
        int count = 0;
        for (int y = 0; y < ROWS; y++) {
            for (int x = 0; x < COLS; x++) {
                if (!snake.contains(cell(x, y))) {
                    if (count == index) {
                        foodX = x;
                        foodY = y;
                        return;
                    }
                    count++;
                }
            }
        }
    }

    // ---------- 坐标与格子索引互转 ----------

    private static int cell(int x, int y) {
        return y * COLS + x;
    }

    private static int xOf(int c) {
        return c % COLS;
    }

    private static int yOf(int c) {
        return c / COLS;
    }

    // ---------- 绘制 ----------

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2 = (Graphics2D) g.create();
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        drawGrid(g2);
        drawFood(g2);
        drawSnake(g2);
        drawScore(g2);

        if (state != State.RUNNING) {
            drawOverlay(g2);
        }
        g2.dispose();
    }

    private void drawGrid(Graphics2D g2) {
        g2.setColor(new Color(255, 255, 255, 12));
        for (int x = 0; x <= COLS; x++) {
            g2.drawLine(x * CELL_SIZE, 0, x * CELL_SIZE, HEIGHT);
        }
        for (int y = 0; y <= ROWS; y++) {
            g2.drawLine(0, y * CELL_SIZE, WIDTH, y * CELL_SIZE);
        }
    }

    private void drawFood(Graphics2D g2) {
        int px = foodX * CELL_SIZE;
        int py = foodY * CELL_SIZE;
        g2.setColor(new Color(231, 76, 60));
        g2.fillOval(px + 4, py + 4, CELL_SIZE - 8, CELL_SIZE - 8);
        g2.setColor(new Color(46, 204, 113));
        // 画一片小叶子作为装饰
        g2.fillOval(px + CELL_SIZE / 2 - 2, py + 1, 7, 4);
    }

    private void drawSnake(Graphics2D g2) {
        int index = 0;
        for (int part : snake) {
            int px = xOf(part) * CELL_SIZE;
            int py = yOf(part) * CELL_SIZE;

            if (index == 0) {
                g2.setColor(new Color(60, 200, 120));
            } else {
                // 身体由亮到暗渐变
                int fade = Math.min(90, index * 4);
                g2.setColor(new Color(70 - fade / 3, 190 - fade, 110 - fade / 3));
            }
            g2.fillRoundRect(px + 2, py + 2, CELL_SIZE - 4, CELL_SIZE - 4, 10, 10);

            if (index == 0) {
                drawEyes(g2, px, py);
            }
            index++;
        }
    }

    private void drawEyes(Graphics2D g2, int px, int py) {
        g2.setColor(Color.WHITE);
        int s = CELL_SIZE;
        int eye = 6;
        switch (direction) {
            case UP -> {
                g2.fillOval(px + 5, py + 5, eye, eye);
                g2.fillOval(px + s - 11, py + 5, eye, eye);
            }
            case DOWN -> {
                g2.fillOval(px + 5, py + s - 11, eye, eye);
                g2.fillOval(px + s - 11, py + s - 11, eye, eye);
            }
            case LEFT -> {
                g2.fillOval(px + 5, py + 5, eye, eye);
                g2.fillOval(px + 5, py + s - 11, eye, eye);
            }
            default -> {
                g2.fillOval(px + s - 11, py + 5, eye, eye);
                g2.fillOval(px + s - 11, py + s - 11, eye, eye);
            }
        }
    }

    private void drawScore(Graphics2D g2) {
        g2.setColor(Color.WHITE);
        g2.setFont(new Font("微软雅黑", Font.BOLD, 16));
        g2.drawString("得分: " + score, 12, 24);
        FontMetrics fm = g2.getFontMetrics();
        String high = "最高分: " + highScore;
        g2.drawString(high, WIDTH - fm.stringWidth(high) - 12, 24);
    }

    /** 绘制开始 / 暂停 / 结束时的半透明提示层 */
    private void drawOverlay(Graphics2D g2) {
        g2.setColor(new Color(0, 0, 0, 150));
        g2.fillRect(0, 0, WIDTH, HEIGHT);

        String title;
        String tip;
        switch (state) {
            case READY -> {
                title = "贪吃蛇";
                tip = "按方向键 / WASD / 空格 开始，也可以点击鼠标";
            }
            case PAUSED -> {
                title = "已暂停";
                tip = "按空格键继续";
            }
            default -> {
                title = "游戏结束";
                tip = "得分 " + score + "，按回车或点击鼠标重新开始";
            }
        }

        g2.setColor(Color.WHITE);
        g2.setFont(new Font("微软雅黑", Font.BOLD, 42));
        FontMetrics fm = g2.getFontMetrics();
        g2.drawString(title, (WIDTH - fm.stringWidth(title)) / 2, HEIGHT / 2 - 20);

        g2.setFont(new Font("微软雅黑", Font.PLAIN, 18));
        fm = g2.getFontMetrics();
        g2.setColor(new Color(220, 220, 220));
        g2.drawString(tip, (WIDTH - fm.stringWidth(tip)) / 2, HEIGHT / 2 + 22);

        if (state == State.READY) {
            // 已禁用输入法，正常无需切英文；保留提示作为兜底
            g2.setFont(new Font("微软雅黑", Font.PLAIN, 13));
            fm = g2.getFontMetrics();
            String note = "提示：若 WASD 无响应，请确认已切换到英文输入法（方向键不受输入法影响）";
            g2.setColor(new Color(160, 160, 160));
            g2.drawString(note, (WIDTH - fm.stringWidth(note)) / 2, HEIGHT / 2 + 56);
        }
    }

    /** 程序入口：创建窗口并启动游戏 */
    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            JFrame frame = new JFrame("贪吃蛇 - Java Swing");
            frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
            frame.setResizable(false);
            frame.add(new SnakeGame());
            frame.pack();
            frame.setLocationRelativeTo(null);
            frame.setVisible(true);
            System.out.println("贪吃蛇已启动：方向键 / WASD / 空格 开始，空格暂停，回车重开。");
        });
    }
}
